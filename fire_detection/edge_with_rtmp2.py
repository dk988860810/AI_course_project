import cv2
from ultralytics import YOLO
import socketio
import pickle
import time
import threading
import subprocess

# 将 <SERVER_IP> 替换为服务器的IP地址
SERVER_IP = '13.214.171.73'
SERVER_PORT = 5001

# 初始化摄像头和YOLO模型
camera = cv2.VideoCapture("testvideo.mp4")  # 替换0为适当的摄像头索引
model = YOLO("model/best.pt")

# 创建一个SocketIO客户端实例
sio = socketio.Client()

# 连接到服务器
sio.connect(f'http://{SERVER_IP}:{SERVER_PORT}')

@sio.event
def connect():
    print('已连接到服务器')

@sio.event
def disconnect():
    print('已从服务器断开连接')

class EdgeComputing:
    def __init__(self, camera, model, edge_id):
        self.cap = camera
        self.model = model
        self.class_label_set = []
        self.start_time = time.time()
        self.frame_counter = 0
        self.stop_event = threading.Event()
        self.edge_id = edge_id

        # Initialize rtmp_process
        rtmp_url = "rtmp://13.214.171.73:1937/fire2/stream_2"
        rtmp_command = [
            "ffmpeg",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", "640x480",
            "-r", "10",
            "-i", "-",
            "-b:v","300k",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-f", "flv",
            rtmp_url
        ]
        self.rtmp_process = subprocess.Popen(rtmp_command, stdin=subprocess.PIPE)

        # Start the RTMP thread
        self.rtmp_thread = threading.Thread(target=self.run_rtmp)
        self.rtmp_thread.start()

    def run_rtmp(self):
        while not self.stop_event.is_set():
            pass  # Add your RTMP streaming logic here if needed

    def detect_objects(self, frame):
        pre_result_cam = self.model.predict(frame, verbose=False)
        self.class_label_set = []
        for data in pre_result_cam[0].boxes:
            x1, y1, x2, y2 = data.xyxy[0]
            class_id = int(data.cls)
            class_label = pre_result_cam[0].names[class_id]
            class_conf = "{:.2f}".format(float(data.conf))
            if data.conf >= 0.5:
                self.class_label_set.append(f'{class_label}')
                org = (int(x1), int(y1))
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                color = (255, 0, 0)
                thickness = 2
                output_text = f'{class_label} {class_conf}'
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 3)
                cv2.putText(frame, output_text, org, font, fontScale, color, thickness)
        return frame

    def stream_video(self):
        try:
            while not self.stop_event.is_set():
                success, frame = self.cap.read()
                if success:
                    #frame_with_detections = self.detect_objects(frame)
                    self.rtmp_process.stdin.write(frame.tobytes())

                    class_labels_bytes = pickle.dumps(self.class_label_set)
                    data = pickle.dumps([self.edge_id, class_labels_bytes], protocol=0)
                    sio.emit('video_frame', data)

                    self.frame_counter += 1

                    current_time = time.time()
                    elapsed_time = current_time - self.start_time

                    if elapsed_time >= 1.0:
                        fps = self.frame_counter / elapsed_time
                        print(f"每秒帧数: {fps}")
                        self.frame_counter = 0
                        self.start_time = time.time()
        except KeyboardInterrupt:
            print("收到键盘中断信号，正在停止...")
            self.stop_event.set()
            self.rtmp_process.stdin.close()
            self.rtmp_process.wait()

if __name__ == "__main__":
    edge_id = 2
    edge_computing = EdgeComputing(camera, model, edge_id)
    stream_thread = threading.Thread(target=edge_computing.stream_video)
    stream_thread.start()

    # 保持主线程运行，同时允许处理其他事件
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("主线程收到键盘中断信号，正在停止...")
        edge_computing.stop_event.set()  # 设置事件对象以通知线程终止
        edge_computing.rtmp_process.stdin.close()  # 关闭FFmpeg stdin
        edge_computing.rtmp_process.wait()  # 等待RTMP进程完成
        stream_thread.join()  # 等待流线程完成
        camera.release()
        sio.disconnect()