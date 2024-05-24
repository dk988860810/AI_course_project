import pandas as pd
import mysql.connector
from flask import request, Response, jsonify, url_for
import shutil
import time
from flask import redirect
from flask import Flask, render_template
import os
import dlib
import csv
import numpy as np
import logging
import cv2
import threading

# Dlib 正向人脸检测器 / Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()

# Dlib 人脸 landmark 特征点检测器 / Get face landmarks
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

# Dlib Resnet 人脸识别模型, 提取 128D 的特征矢量 / Use Dlib resnet50 model to get 128D face descriptor
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")


class Face_Recognizer:
    def __init__(self):
        self.font = cv2.FONT_ITALIC

        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.fps_show = 0
        self.start_time = time.time()

        # cnt for frame
        self.frame_cnt = 0

        # 用来存放所有录入人脸特征的数组 / Save the features of faces in the database
        self.face_features_known_list = []
        # 存储录入人脸名字 / Save the name of faces in the database
        self.face_name_known_list = []

        # 用来存储上一帧和当前帧 ROI 的质心坐标 / List to save centroid positions of ROI in frame N-1 and N
        self.last_frame_face_centroid_list = []
        self.current_frame_face_centroid_list = []

        # 用来存储上一帧和当前帧检测出目标的名字 / List to save names of objects in frame N-1 and N
        self.last_frame_face_name_list = []
        self.current_frame_face_name_list = []

        # 上一帧和当前帧中人脸数的计数器 / cnt for faces in frame N-1 and N
        self.last_frame_face_cnt = 0
        self.current_frame_face_cnt = 0

        # 用来存放进行识别时候对比的欧氏距离 / Save the e-distance for faceX when recognizing
        self.current_frame_face_X_e_distance_list = []

        # 存储当前摄像头中捕获到的所有人脸的坐标名字 / Save the positions and names of current faces captured
        self.current_frame_face_position_list = []
        # 存储当前摄像头中捕获到的人脸特征 / Save the features of people in current frame
        self.current_frame_face_feature_list = []

        # e distance between centroid of ROI in last and current frame
        self.last_current_frame_centroid_e_distance = 0

        # 控制再识别的后续帧数 / Reclassify after 'reclassify_interval' frames
        # 如果识别出 "unknown" 的脸, 将在 reclassify_interval_cnt 计数到 reclassify_interval 后, 对于人脸进行重新识别
        self.reclassify_interval_cnt = 0
        self.reclassify_interval = 10

    # 从 "features_all.csv" 读取录入人脸特征 / Get known faces from "features_all.csv"
    def get_face_database(self):
        if os.path.exists("data/features_all.csv"):
            path_features_known_csv = "data/features_all.csv"
            csv_rd = pd.read_csv(path_features_known_csv, header=None)
            for i in range(csv_rd.shape[0]):
                features_someone_arr = []
                self.face_name_known_list.append(csv_rd.iloc[i][0])
                for j in range(1, 129):
                    if csv_rd.iloc[i][j] == '':
                        features_someone_arr.append('0')
                    else:
                        features_someone_arr.append(csv_rd.iloc[i][j])
                self.face_features_known_list.append(features_someone_arr)
            logging.info("Faces in Database： %d", len(self.face_features_known_list))
            return 1
        else:
            logging.warning("'features_all.csv' not found!")
            logging.warning("Please run 'get_faces_from_camera.py' "
                            "and 'features_extraction_to_csv.py' before 'face_reco_from_camera.py'")
            return 0

    def update_fps(self):
        now = time.time()
        # 每秒刷新 fps / Refresh fps per second
        if str(self.start_time).split(".")[0] != str(now).split(".")[0]:
            self.fps_show = self.fps
        self.start_time = now
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now

    @staticmethod
    # 计算两个128D向量间的欧式距离 / Compute the e-distance between two 128D features
    def return_euclidean_distance(feature_1, feature_2):
        feature_1 = np.array(feature_1)
        feature_2 = np.array(feature_2)
        dist = np.sqrt(np.sum(np.square(feature_1 - feature_2)))
        return dist

    # 使用质心追踪来识别人脸 / Use centroid tracker to link face_x in current frame with person_x in last frame
    def centroid_tracker(self):
        for i in range(len(self.current_frame_face_centroid_list)):
            e_distance_current_frame_person_x_list = []
            # 对于当前帧中的人脸1, 和上一帧中的 人脸1/2/3/4/.. 进行欧氏距离计算 / For object 1 in current_frame, compute e-distance with object 1/2/3/4/... in last frame
            for j in range(len(self.last_frame_face_centroid_list)):
                self.last_current_frame_centroid_e_distance = self.return_euclidean_distance(
                    self.current_frame_face_centroid_list[i], self.last_frame_face_centroid_list[j])

                e_distance_current_frame_person_x_list.append(
                    self.last_current_frame_centroid_e_distance)

            last_frame_num = e_distance_current_frame_person_x_list.index(
                min(e_distance_current_frame_person_x_list))
            self.current_frame_face_name_list[i] = self.last_frame_face_name_list[last_frame_num]

    # 生成的 cv2 window 上面添加说明文字 / putText on cv2 window
    def draw_note(self, img_rd):
        # 添加说明 / Add some info on windows
        cv2.putText(img_rd, "Face Recognizer with OT", (20, 40), self.font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(img_rd, "Frame:  " + str(self.frame_cnt), (20, 100), self.font, 0.8, (0, 255, 0), 1,
                    cv2.LINE_AA)
        cv2.putText(img_rd, "FPS:    " + str(self.fps.__round__(2)), (20, 130), self.font, 0.8, (0, 255, 0), 1,
                    cv2.LINE_AA)
        cv2.putText(img_rd, "Faces:  " + str(self.current_frame_face_cnt), (20, 160), self.font, 0.8, (0, 255, 0), 1,
                    cv2.LINE_AA)
        cv2.putText(img_rd, "Q: Quit", (20, 450), self.font, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        for i in range(len(self.current_frame_face_name_list)):
            img_rd = cv2.putText(img_rd, "Face_" + str(i + 1), tuple(
                [int(self.current_frame_face_centroid_list[i][0]), int(self.current_frame_face_centroid_list[i][1])]),
                                 self.font,
                                 0.8, (255, 190, 0),
                                 1,
                                 cv2.LINE_AA)

    # 处理获取的视频流, 进行人脸识别 / Face detection and recognition wit OT from input video stream
    def process(self, stream):
        # 1. 读取存放所有人脸特征的 csv / Get faces known from "features.all.csv"
        if self.get_face_database():
            while stream.isOpened():
                face_found = False
                self.frame_cnt += 1
                logging.debug("Frame " + str(self.frame_cnt) + " starts")
                flag, img_rd = stream.read()
                kk = cv2.waitKey(1)

                # 2. 检测人脸 / Detect faces for frame X
                faces = detector(img_rd, 0)

                # 3. 更新人脸计数器 / Update cnt for faces in frames
                self.last_frame_face_cnt = self.current_frame_face_cnt
                self.current_frame_face_cnt = len(faces)

                # 4. 更新上一帧中的人脸列表 / Update the face name list in last frame
                self.last_frame_face_name_list = self.current_frame_face_name_list[:]

                # 5. 更新上一帧和当前帧的质心列表 / update frame centroid list
                self.last_frame_face_centroid_list = self.current_frame_face_centroid_list
                self.current_frame_face_centroid_list = []

                # 6.1 如果当前帧和上一帧人脸数没有变化 / if cnt not changes
                if (self.current_frame_face_cnt == self.last_frame_face_cnt) and (
                        self.reclassify_interval_cnt != self.reclassify_interval):
                    logging.debug(
                        "scene 1: 当前帧和上一帧相比没有发生人脸数变化 / No face cnt changes in this frame!!!")

                    self.current_frame_face_position_list = []

                    if "unknown" in self.current_frame_face_name_list:
                        logging.debug("  有未知人脸, 开始进行 reclassify_interval_cnt 计数")
                        self.reclassify_interval_cnt += 1

                    if self.current_frame_face_cnt != 0:
                        for k, d in enumerate(faces):
                            self.current_frame_face_position_list.append(tuple(
                                [faces[k].left(), int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4)]))
                            self.current_frame_face_centroid_list.append(
                                [int(faces[k].left() + faces[k].right()) / 2,
                                 int(faces[k].top() + faces[k].bottom()) / 2])

                            img_rd = cv2.rectangle(img_rd,
                                                   tuple([d.left(), d.top()]),
                                                   tuple([d.right(), d.bottom()]),
                                                   (255, 255, 255), 2)

                    # 如果当前帧中有多个人脸, 使用质心追踪 / Multi-faces in current frame, use centroid-tracker to track
                    if self.current_frame_face_cnt != 1:
                        self.centroid_tracker()

                    for i in range(self.current_frame_face_cnt):
                        # 6.2 Write names under ROI
                        img_rd = cv2.putText(img_rd, self.current_frame_face_name_list[i],
                                             self.current_frame_face_position_list[i], self.font, 0.8, (0, 255, 255), 1,
                                             cv2.LINE_AA)
                    self.draw_note(img_rd)

                    if "unknown" not in self.current_frame_face_name_list and self.current_frame_face_name_list:
                        face_found = True
                        # print('flag true')
                        # print(self.current_frame_face_name_list)
                    else:
                        face_found = False
                    # print(self.current_frame_face_name_list)

                # 6.2 如果当前帧和上一帧人脸数发生变化 / If cnt of faces changes, 0->1 or 1->0 or ...
                else:
                    logging.debug("scene 2: 当前帧和上一帧相比人脸数发生变化 / Faces cnt changes in this frame")
                    self.current_frame_face_position_list = []
                    self.current_frame_face_X_e_distance_list = []
                    self.current_frame_face_feature_list = []
                    self.reclassify_interval_cnt = 0

                    # 6.2.1 人脸数减少 / Face cnt decreases: 1->0, 2->1, ...
                    if self.current_frame_face_cnt == 0:
                        logging.debug("  scene 2.1 人脸消失, 当前帧中没有人脸 / No faces in this frame!!!")
                        # clear list of names and features
                        self.current_frame_face_name_list = []
                    # 6.2.2 人脸数增加 / Face cnt increase: 0->1, 0->2, ..., 1->2, ...
                    else:
                        logging.debug(
                            "  scene 2.2 出现人脸, 进行人脸识别 / Get faces in this frame and do face recognition")
                        self.current_frame_face_name_list = []
                        for i in range(len(faces)):
                            shape = predictor(img_rd, faces[i])
                            self.current_frame_face_feature_list.append(
                                face_reco_model.compute_face_descriptor(img_rd, shape))
                            self.current_frame_face_name_list.append("unknown")

                        # 6.2.2.1 遍历捕获到的图像中所有的人脸 / Traversal all the faces in the database
                        for k in range(len(faces)):
                            logging.debug("  For face %d in current frame:", k + 1)
                            self.current_frame_face_centroid_list.append(
                                [int(faces[k].left() + faces[k].right()) / 2,
                                 int(faces[k].top() + faces[k].bottom()) / 2])

                            self.current_frame_face_X_e_distance_list = []

                            # 6.2.2.2 每个捕获人脸的名字坐标 / Positions of faces captured
                            self.current_frame_face_position_list.append(tuple(
                                [faces[k].left(), int(faces[k].bottom() + (faces[k].bottom() - faces[k].top()) / 4)]))

                            # 6.2.2.3 对于某张人脸, 遍历所有存储的人脸特征
                            # For every faces detected, compare the faces in the database
                            for i in range(len(self.face_features_known_list)):
                                # 如果 q 数据不为空
                                if str(self.face_features_known_list[i][0]) != '0.0':
                                    e_distance_tmp = self.return_euclidean_distance(
                                        self.current_frame_face_feature_list[k],
                                        self.face_features_known_list[i])
                                    logging.debug("      with person %d, the e-distance: %f", i + 1, e_distance_tmp)
                                    self.current_frame_face_X_e_distance_list.append(e_distance_tmp)
                                else:
                                    # 空数据 person_X
                                    self.current_frame_face_X_e_distance_list.append(999999999)

                            # 6.2.2.4 寻找出最小的欧式距离匹配 / Find the one with minimum e distance
                            similar_person_num = self.current_frame_face_X_e_distance_list.index(
                                min(self.current_frame_face_X_e_distance_list))

                            if min(self.current_frame_face_X_e_distance_list) < 0.4:
                                self.current_frame_face_name_list[k] = self.face_name_known_list[similar_person_num]
                                logging.debug("  Face recognition result: %s",
                                              self.face_name_known_list[similar_person_num])
                                # print('找到')
                            else:
                                logging.debug("  Face recognition result: Unknown person")
                        # 7. 生成的窗口添加说明文字 / Add note on cv2 window
                        self.draw_note(img_rd)

                        # cv2.imwrite("debug/debug_" + str(self.frame_cnt) + ".png", img_rd) # Dump current frame image if needed

                # 8. 按下 'q' 键退出 / Press 'q' to exit
                if kk == ord('q'):
                    break

                self.update_fps()
                # cv2.namedWindow("camera", 1)
                # cv2.imshow("camera", img_rd)

                # 将画面转换为 JPEG 格式
                ret, buffer = cv2.imencode('.jpg', img_rd)
                img_rd = buffer.tobytes()
                #
                # # 以字节流形式返回画面
                if self.current_frame_face_name_list:
                    name_list = self.current_frame_face_name_list[0]
                else:
                    name_list = ["unknown"]
                yield img_rd, face_found, name_list
                # yield (b'--frame\r\n'
                #        b'Content-Type: image/jpeg\r\n\r\n' + img_rd + b'\r\n')

                logging.debug("Frame ends\n\n")
    def run(self):
        # cap = cv2.VideoCapture("video.mp4")  # Get video stream from video file
        cap = cv2.VideoCapture('rtmp://13.214.171.73/face/aws')  # Get video stream from camera
        self.process(cap)

        cap.release()
        cv2.destroyAllWindows()


def main():
    # logging.basicConfig(level=logging.DEBUG) # Set log level to 'logging.DEBUG' to print debug info of every frame
    logging.basicConfig(level=logging.INFO)
    Face_Recognizer_con = Face_Recognizer()
    Face_Recognizer_con.run()


ff_flag = False
name_list=['unknown']
def generate_frames():
    global ff_flag, name_list, cap
    face_recognizer = Face_Recognizer()
    for frame, face_found, name_list in face_recognizer.process(cap):
        ff_flag = False
        # print('face_found = ',face_found)
        if face_found:
            ff_flag = True
            # print(ff_flag)
            # print(name_list)
        # else:
        #     ff_flag = False
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# Dlib 正向人脸检测器 / Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()

# 全局变量 / Global variables
current_frame_faces_cnt = 0  # 当前帧中人脸计数器 / cnt for counting faces in current frame
existing_faces_cnt = 0  # 已录入的人脸计数器 / cnt for counting saved faces
ss_cnt = 0  # 录入 person_n 人脸时图片计数器 / cnt for screen shots

path_photos_from_camera = "data/data_faces_from_camera/"
current_face_dir = ""
font = cv2.FONT_ITALIC

# Current frame and face ROI position
current_frame = np.ndarray
face_ROI_image = np.ndarray
face_ROI_width_start = 0
face_ROI_height_start = 0
face_ROI_width = 0
face_ROI_height = 0
ww = 0
hh = 0

out_of_range_flag = False
face_folder_created_flag = False

# FPS
frame_time = 0
frame_start_time = 0
fps = 0
fps_show = 0
start_time = time.time()



# 删除之前存的人脸数据文件夹 / Delete old face folders
def clear_data():
    # 删除之前存的人脸数据文件夹, 删除 "/data_faces_from_camera/person_x/"...
    folders_rd = os.listdir(path_photos_from_camera)
    for i in range(len(folders_rd)):
        shutil.rmtree(path_photos_from_camera + folders_rd[i])
    if os.path.isfile("data/features_all.csv"):
        os.remove("data/features_all.csv")
    return "Face images and `features_all.csv` removed!"


# 新建保存人脸图像文件和数据 CSV 文件夹 / Mkdir for saving photos and csv
def pre_work_mkdir():
    # 新建文件夹 / Create folders to save face images and csv
    if os.path.isdir(path_photos_from_camera):
        pass
    else:
        os.mkdir(path_photos_from_camera)


# 如果有之前录入的人脸, 在之前 person_x 的序号按照 person_x+1 开始录入 / Start from person_x+1
def check_existing_faces_cnt():
    global existing_faces_cnt
    if os.listdir("data/data_faces_from_camera/"):
        # 获取已录入的最后一个人脸序号 / Get the order of latest person
        person_list = os.listdir("data/data_faces_from_camera/")
        person_num_list = []
        for person in person_list:
            person_order = person.split('_')[1].split('_')[0]
            person_num_list.append(int(person_order))
        existing_faces_cnt = max(person_num_list)

    # 如果第一次存储或者没有之前录入的人脸, 按照 person_1 开始录入 / Start from person_1
    else:
        existing_faces_cnt = 0


# 更新 FPS / Update FPS of Video stream
def update_fps():
    global frame_time, fps, fps_show, start_time, frame_start_time

    now = time.time()
    frame_time = now - frame_start_time

    if frame_time != 0:
        fps = 1.0 / frame_time
    else:
        fps = 0

    # 每秒刷新 fps / Refresh fps per second
    if str(start_time).split(".")[0] != str(now).split(".")[0]:
        fps_show = fps
    start_time = now
    frame_start_time = now


# 创建人脸文件夹 / Create the folders for saving faces
def create_face_folder(name):
    global existing_faces_cnt, ss_cnt, current_face_dir, face_folder_created_flag
    existing_faces_cnt += 1
    if name:
        current_face_dir = path_photos_from_camera + \
                            "person_" + str(existing_faces_cnt) + "_" + \
                            name
    else:
        current_face_dir = path_photos_from_camera + \
                            "person_" + str(existing_faces_cnt)
    os.makedirs(current_face_dir)
    ss_cnt = 0  # 将人脸计数器清零 / Clear the cnt of screen shots
    face_folder_created_flag = True  # Face folder already created
    return "\"" + current_face_dir + "/\" created!"


# 保存当前人脸 / Save current face in frame
def save_current_face():
    global out_of_range_flag, current_frame_faces_cnt, ss_cnt, face_ROI_image, current_frame

    if face_folder_created_flag:
        if current_frame_faces_cnt == 1:
            if not out_of_range_flag:
                ss_cnt += 1
                # 根据人脸大小生成空的图像 / Create blank image according to the size of face detected
                face_ROI_image = np.zeros((int(face_ROI_height * 2), face_ROI_width * 2, 3),
                                          np.uint8)
                for ii in range(face_ROI_height * 2):
                    for jj in range(face_ROI_width * 2):
                        face_ROI_image[ii][jj] = current_frame[face_ROI_height_start - hh +
                                                               ii][face_ROI_width_start - ww + jj]
                filename = current_face_dir + "/img_face_" + str(ss_cnt) + ".jpg"
                # cv2.imwrite(filename, cv2.cvtColor(face_ROI_image, cv2.COLOR_RGB2BGR))
                cv2.imwrite(filename, face_ROI_image)
                return "\"" + filename + "\" saved!"
            else:
                return "Please do not out of range!"
        else:
            return "No face in current frame!"
    else:
        return "Please run step 2!"

label_warning = ''
# 获取人脸 / Main process of face detection and saving
def process(cap):
    global current_frame, current_frame_faces_cnt, face_ROI_height, face_ROI_width, \
        face_ROI_height_start, face_ROI_width_start, ww, hh, out_of_range_flag
    global label_warning

    ret, current_frame = cap.read()
    faces = detector(current_frame, 0)

    if ret:
        update_fps()
        # 检测到人脸 / Face detected
        if len(faces) != 0:
            current_frame_faces_cnt = len(faces)
            # 矩形框 / Show the ROI of faces
            for k, d in enumerate(faces):
                face_ROI_width
                face_ROI_width_start = d.left()
                face_ROI_height_start = d.top()
                # 计算矩形框大小 / Compute the size of rectangle box
                face_ROI_height = (d.bottom() - d.top())
                face_ROI_width = (d.right() - d.left())
                hh = int(face_ROI_height / 2)
                ww = int(face_ROI_width / 2)

                # 判断人脸矩形框是否超出 480x640 / If the size of ROI > 480x640
                if (d.right() + ww) > 640 or (d.bottom() + hh > 480) or (d.left() - ww < 0) or (
                        d.top() - hh < 0):
                    out_of_range_flag = True
                    label_warning = "OUT OF RANGE"
                else:
                    out_of_range_flag = False
                    label_warning = 'IN RANGE'

                current_frame = cv2.rectangle(current_frame,
                                              tuple([d.left() - ww, d.top() - hh]),
                                              tuple([d.right() + ww, d.bottom() + hh]),
                                              (255, 255, 255) if not out_of_range_flag else (0, 0, 255), 2)

    return current_frame, label_warning

# 要读取人脸图像文件的路径 / Path of cropped faces
path_images_from_camera = "data/data_faces_from_camera/"

# Dlib 人脸 landmark 特征点检测器 / Get face landmarks
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

# Dlib Resnet 人脸识别模型，提取 128D 的特征矢量 / Use Dlib resnet50 model to get 128D face descriptor
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

# 返回单张图像的 128D 特征 / Return 128D features for single image
# Input:    path_img           <class 'str'>
# Output:   face_descriptor    <class 'dlib.vector'>
def return_128d_features(path_img):
    img_rd = cv2.imread(path_img)
    faces = detector(img_rd, 1)

    logging.info("%-40s %-20s", "检测到人脸的图像 / Image with faces detected:", path_img)

    # 因为有可能截下来的人脸再去检测，检测不出来人脸了, 所以要确保是 检测到人脸的人脸图像拿去算特征
    # For photos of faces saved, we need to make sure that we can detect faces from the cropped images
    if len(faces) != 0:
        shape = predictor(img_rd, faces[0])
        face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
    else:
        face_descriptor = 0
        logging.warning("no face")
    return face_descriptor

# 返回 personX 的 128D 特征均值 / Return the mean value of 128D face descriptor for person X
# Input:    path_face_personX        <class 'str'>
# Output:   features_mean_personX    <class 'numpy.ndarray'>
def return_features_mean_personX(path_face_personX):
    features_list_personX = []
    photos_list = os.listdir(path_face_personX)
    if photos_list:
        for i in range(len(photos_list)):
            # 调用 return_128d_features() 得到 128D 特征 / Get 128D features for single image of personX
            logging.info("%-40s %-20s", "正在读的人脸图像 / Reading image:", path_face_personX + "/" + photos_list[i])
            features_128d = return_128d_features(path_face_personX + "/" + photos_list[i])
            # 遇到没有检测出人脸的图片跳过 / Jump if no face detected from image
            if features_128d == 0:
                i += 1
            else:
                features_list_personX.append(features_128d)
    else:
        logging.warning("文件夹内图像文件为空 / Warning: No images in%s/", path_face_personX)

    # 计算 128D 特征的均值 / Compute the mean
    # personX 的 N 张图像 x 128D -> 1 x 128D
    if features_list_personX:
        features_mean_personX = np.array(features_list_personX, dtype=object).mean(axis=0)
    else:
        features_mean_personX = np.zeros(128, dtype=object, order='C')
    return features_mean_personX

app = Flask(__name__)
app.secret_key = 'mmm'

@app.route('/get_ff_flag')
def get_ff_flag():
    global ff_flag, name_list
    return jsonify({'ff_flag': ff_flag, 'name_list': name_list})


@app.route('/index')
def index():
    # 使用 HTML 模板渲染页面
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    # 返回生成的帧
    stream_fr = generate_frames()
    return Response(stream_fr, mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_face')
def get_face():
    return render_template('get_face.html')

@app.route('/face_recognition')
def start_video():
    return render_template('face_reco_from_camera_ot.html')


@app.route('/face_reco_suc')
def face_reco_suc():
    return render_template('face_reco_suc.html')

@app.route('/test_mysql')
def test_mysql():
    return render_template('test_mysql.html')


# 数据库连接配置
db_config = {
    'host': '54.162.189.102',
    'user': 'test_user',
    'password': 'testpassword',
    'database': 'aws_test',
    'auth_plugin': 'mysql_native_password'
}

# 读写mysql
# 处理打卡请求
@app.route('/clock_in', methods=['POST'])
def clock_in():
    # 获取请求中的姓名
    data = request.json
    name = data['name']
    print(name)
    # 连接数据库
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 查询数据库中{name}的信息
        query = f"SELECT * FROM users WHERE name = '{name}'"
        cursor.execute(query)
        user = cursor.fetchone()
        # print(user)
        if user:
            clock_status_index = cursor.column_names.index('clock_status')
            if user[clock_status_index] != 'Clock In':
                # 清空下班打卡时间和状态，并更新上班打卡时间和状态
                update_query = f"UPDATE users SET clock_in_time = CONVERT_TZ(UTC_TIMESTAMP(), '+00:00', '+08:00'), clock_status = 'Clock In' WHERE name = '{name}'"
                cursor.execute(update_query)
                conn.commit()
                message = '打卡成功'
            else:
                # 清空上班打卡时间和状态，并更新下班打卡时间和状态
                update_query = f"UPDATE users SET clock_in_time = CONVERT_TZ(UTC_TIMESTAMP(), '+00:00', '+08:00'), clock_status = 'Clock Out' WHERE name = '{name}'"
                cursor.execute(update_query)
                conn.commit()
                message = '下班'
        else:
            message = '找不到该用户'

        cursor.close()
        conn.close()

        return jsonify({'message': message})

    except Exception as e:
        return jsonify({'message': str(e)})

@app.route('/clear_data', methods=['POST'])
def clear_data_route():
    return clear_data()


@app.route('/input_name', methods=['POST'])
def input_name():
    global get_input_name
    name = request.form['name']
    print('route_sf')
    get_input_name = create_face_folder(name)
    return get_input_name


@app.route('/save_face', methods=['POST'])
def save_face():
    return save_current_face()

stop_video_stream = False
def gen():
    global frame_start_time, label_warning,cap
    frame_start_time = time.time()
    while not stop_video_stream:
        frame, label_warning = process(cap)
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 转换图像颜色为RGB
        frame = cv2.resize(frame, (640, 480))
        update_fps()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')



@app.route('/video_feed_gf')
def video_feed_gf():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_label_warning')
def get_label_warning():
    global label_warning
    return jsonify({'label_warning': label_warning})

@app.route('/stop_video_capture')
def stop_video_capture():
    # 在这里添加停止视频捕获的代码
    cap.release()
    return


@app.route('/features_extraction')
def features_extraction():
    global stop_video_stream
    stop_video_stream = True
    time.sleep(2)
    logging.basicConfig(level=logging.INFO)
    # 获取已录入的最后一个人脸序号 / Get the order of latest person
    person_list = os.listdir("data/data_faces_from_camera/")
    person_list.sort()
    with open("data/features_all.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for person in person_list:
            # Get the mean/average features of face/personX, it will be a list with a length of 128D
            logging.info("%sperson_%s", path_images_from_camera, person)
            features_mean_personX = return_features_mean_personX(path_images_from_camera + person)

            if len(person.split('_', 2)) == 2:
                # "person_x"
                person_name = person
            else:
                # "person_x_tom"
                person_name = person.split('_', 2)[-1]
            features_mean_personX = np.insert(features_mean_personX, 0, person_name, axis=0)
            # features_mean_personX will be 129D, person name + 128 feautres
            writer.writerow(features_mean_personX)
            logging.info('\n')
        logging.info("所有录入人脸数据存入 / Save all the features of faces registered into: data/features_all.csv")

    return "Features extracted and saved into 'data/features_all.csv' successfully!"

# 打卡名单 表格
@app.route('/user_form')
def user_form():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 计算总条目数
        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]
        total_pages = (total_count + per_page - 1) // per_page

        # 查询当前页的数据
        offset = (page - 1) * per_page
        cursor.execute("SELECT * FROM users LIMIT %s OFFSET %s", (per_page, offset))
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('user_form.html', users=users, page=page, total_pages=total_pages)
    except Exception as e:
        return jsonify({'message': str(e)})


@app.route('/reset_clock_status')
def reset_clock_status():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # 清空clock_in_time和clock_status两列
        query = "UPDATE users SET clock_in_time = NULL, clock_status = NULL"
        cursor.execute(query)
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('user_form'))
    except Exception as e:
        return jsonify({'message': str(e)})


from flask import Flask, request, session, redirect, url_for, render_template, flash
import mysql.connector
import re
import os
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user

# 连接到 MySQL 数据库
conn = mysql.connector.connect(
    host="54.162.189.102",
    user="test_user",
    password="testpassword",
    database="aws_test"
)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM test_accounts WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(int(user["id"]), user["username"], user["role"])
    return None

# 首頁路由
@app.route('/')
def firsthome():
    return render_template('firsthome.html')


# 用於登錄頁面的路由
@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = conn.cursor(dictionary=True)  # 使用字典游標，以便更容易地訪問結果
        cursor.execute('SELECT * FROM test_accounts WHERE username = %s ', (username, ))
        user = cursor.fetchone()
        cursor.close()

        if user and user['password'] == password:  # 检查明文密码
            login_user(User(int(user["id"]), user["password"], user["role"]))
            if user["role"] == 'HR':
                return redirect(url_for('HR'))
            elif user["role"] == 'police':
                return redirect(url_for('police'))
            elif user["role"] == 'fire':
                return redirect(url_for('fire'))
        else:
            msg = '用戶名/密碼不正確！'

    return render_template('login.html', msg=msg)


@app.route('/HR')
@login_required
def HR():
    if current_user.role != 'HR':
        return redirect(url_for('login'))
    return redirect(url_for('profile'))

@app.route('/police')
@login_required
def police():
    if current_user.role != 'police':
        return redirect(url_for('login'))
    return redirect('http://127.0.0.1:5001/')

@app.route('/fire')
@login_required
def fire():
    if current_user.role != 'fire':
        return redirect(url_for('login'))
    return redirect('http://127.0.0.1:5001/table')

# 用於註冊頁面的路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form :
        
        username = request.form['username']
        password = request.form['password']
        role=request.form['role']

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM test_accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        try:
            if account:
                msg = '帳戶已存在！'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = '用戶名必須只包含字母和數字！'
            elif not username or not password :
                msg = '請填寫表單！'
            else:
                cursor.execute('INSERT INTO test_accounts (username, password, role) VALUES ( %s, %s, %s)',
                        ( username, password, role))
        
                conn.commit()
                msg = '您已成功註冊！'
        
        except Exception as e:
            conn.rollback()
            msg = f'發生錯誤：{str(e)}'
        finally:
            cursor.close()
    elif request.method == 'POST':
        msg = '請填寫表單！'

    return render_template('register.html', msg=msg)


# 首頁路由（只有已登錄的用戶可以訪問）
# @app.route('/')
# # def home():
# #     if 'loggedin' in session:
# #         return render_template('HR.html')
# #     return redirect(url_for('login'))

# 登出路由
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('firsthome'))

# 定义一个函数来捕获视频流
def capture_video():
    global cap, stop_video_stream
    cap = cv2.VideoCapture('rtmp://13.214.171.73/face/aws')  # 获取视频流
    # cap = cv2.VideoCapture(0)  # 获取视频流
    stop_video_stream = False

# 用戶資料頁面路由（只有已登錄的用戶可以訪問）
@app.route('/profile')
def profile():
    global cap
    # cap = cv2.VideoCapture('rtmp://13.214.171.73/face/aws')  # Get video stream from camera
    # 在应用程序启动时启动视频捕获线程
    video_thread = threading.Thread(target=capture_video)
    video_thread.start()

    page = request.args.get('page', 1, type=int)
    per_page = 10

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 计算总条目数
        cursor.execute("SELECT COUNT(*) FROM HR_accounts")
        total_count = cursor.fetchone()['COUNT(*)']
        total_pages = (total_count + per_page - 1) // per_page

        # 查询当前页的数据
        offset = (page - 1) * per_page
        cursor.execute("SELECT * FROM HR_accounts LIMIT %s OFFSET %s", (per_page, offset))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('HR.html', rows=rows, page=page, total_pages=total_pages)
    except Exception as e:
        return jsonify({'message': str(e)})


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'loggedin' in session:
        # 獲取從表單提交的更新後的個人資料
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # 處理上傳的照片
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                # 將照片保存到指定目錄
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # 只保存檔名到資料庫中
                profile_picture_path = filename

        # 執行更新個人資料的 SQL 語句
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts 
            SET fullname = %s, username = %s, password = %s, email = %s , profile_picture_path= %s
            WHERE id = %s
        ''', (fullname, username, password, email, profile_picture_path, session['id']))
        conn.commit()
        cursor.close()

        flash('Update success', 'success')
        # 重定向到用戶的個人資料頁面
        return redirect(url_for('profile'))
    else:
        # 如果用戶未登錄，重定向到登錄頁面
        return redirect(url_for('login'))



@app.route('/edit', methods=['POST'])
def edit_employee():
    data = request.form
    emp_id = data['id']
    name = data['name']
    job_title = data['jobTitle']
    department = data['department']
    location = data['location']
    phone = data['phone']
    emergency_contact = data['emergencyContact']
    emergency_phone = data['emergencyPhone']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE HR_accounts 
            SET 姓名 = %s, 職務名稱 = %s, 所屬組別 = %s, 辦公位置 = %s, 聯絡電話 = %s, 緊急聯絡人 = %s, 緊急聯絡人電話 = %s
            WHERE 工號 = %s
        """, (name, job_title, department, location, phone, emergency_contact, emergency_phone, emp_id))

        cursor.execute("""
            UPDATE users 
            SET name = %s, department = %s, position = %s
            WHERE id = %s
        """, (name, job_title, location, emp_id))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM HR_accounts WHERE 工號 = %s", (emp_id,))
        cursor.execute("DELETE FROM users WHERE id = %s", (emp_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('profile'))
    except Exception as e:
        return jsonify({'message': str(e)})


@app.route('/add_employee', methods=['POST'])
def add_employee():
    # 获取表单数据
    job_id = request.form['job_id']

    name = request.form['name']
    job_title = request.form['jobTitle']
    department = request.form['department']
    location = request.form['location']
    phone = request.form['phone']
    emergency_contact = request.form['emergencyContact']
    emergency_phone = request.form['personalFiles']

    # 连接 MySQL 数据库
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    # 构建 SQL 插入语句
    sql = "INSERT INTO HR_accounts (工號, 姓名, 職務名稱, 所屬組別, 辦公位置, 聯絡電話, 緊急聯絡人, 緊急聯絡人電話) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    values = (job_id, name, job_title, department, location, phone, emergency_contact, emergency_phone)
    punchin = "INSERT INTO users (id, name, department, position) VALUES (%s, %s, %s, %s)"
    punchin_value = (job_id, name, job_title, location)
    print(sql)
    try:
        # 执行 SQL 语句
        cursor.execute(sql, values)
        cursor.execute(punchin, punchin_value)
        db.commit()
        print("Data inserted successfully!")
    except mysql.connector.Error as error:
        print(f"Error inserting data: {error}")
    finally:
        # 关闭数据库连接
        cursor.close()
        db.close()

    # 返回响应或重定向到其他页面
    return redirect(url_for('profile'))

check_existing_faces_cnt()
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    pre_work_mkdir()
    check_existing_faces_cnt()
    app.run(debug=True)