from flask import Flask, render_template, Response
import cv2
from threading import Thread
from queue import Queue
from ultralytics import YOLO
from datetime import datetime
import os

app = Flask(__name__)
current_datetime = datetime.now()
formatted_date = current_datetime.strftime("%Y-%m-%d")
formatted_time = current_datetime.strftime("%H-%M-%S")

class Camera:
    def __init__(self, camera_index):
        self.cap = cv2.VideoCapture(camera_index)
        self.frame_queue = Queue()
        self.class_label_set = []
        self.model = YOLO("model/best.pt")

    def detect_objects(self, frame, model):
        pre_result_cam = model.predict(frame)
        self.class_label_set = []
        for data in pre_result_cam[0].boxes:
            x1, y1, x2, y2 = data.xyxy[0]
            class_id = int(data.cls)
            class_label = pre_result_cam[0].names[class_id]
            class_conf = "{:.2f}".format(float(data.conf))
            if data.conf >= 0.5:
                self.class_label_set.append(f'{class_label} {class_conf}')
                org = (int(x1), int(y1))
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                color = (255, 0, 0)
                thickness = 2
                output_text = f'{class_label} {class_conf}'
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 3)
                cv2.putText(frame, output_text, org, font, fontScale, color, thickness)
        return frame
    
    def video_feed_and_save(self, camera_id=None):
        def detect_and_save():
            #count = 0
            # current_datetime = datetime.now()
            # formatted_date = current_datetime.strftime("%Y-%m-%d")
            # formatted_time = current_datetime.strftime("%H-%M-%S")
            path="C:/Users/dk988/Desktop/AI_project_video/camera_"+str(camera_id)
            file_name = "{}/{}_{}.avi".format(path,formatted_date,formatted_time)
            
            # while os.path.exists(file_name):
            #     file_name = "{}/{}.avi".format(path,str(camera_id)+"_"+formatted_date + "_" + str(count))
            #     count += 1

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(file_name, fourcc, 30.0, (640, 480))

            try:
                while True:
                    success, frame = self.cap.read()
        
                    if not success:
                        break
                    else:
                        self.class_label_set = []
                        frame = self.detect_objects(frame, self.model)
                        out.write(frame)
                        self.frame_queue.put(frame)
            finally:
                out.release()

        t = Thread(target=detect_and_save)
        t.start()

    def generate_frames(self):
        while True:
            frame = self.frame_queue.get()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Example usage:
camera_1 = Camera(0)  # First camera
camera_2 = Camera(1)  # Second camera
camera_3 = Camera(2)  # Third camera

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_1')
def video_feed_route_1():
    # t1 = Thread(target=camera_1.video_feed_and_save)
    # t1.start()
    camera_1.video_feed_and_save(camera_id=1)
    return Response(camera_1.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_2')
def video_feed_route_2():
    # t2 = Thread(target=camera_2.video_feed_and_save)
    # t2.start()
    camera_2.video_feed_and_save(camera_id=2)
    return Response(camera_2.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_3')
def video_feed_route_3():
    # t3 = Thread(target=camera_3.video_feed_and_save)
    # t3.start()
    camera_3.video_feed_and_save(camera_id=3)
    return Response(camera_3.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_class_label_1')
def get_class_label_1():
    global camera_1
    return ' '.join(camera_1.class_label_set)

@app.route('/get_class_label_2')
def get_class_label_2():
    global camera_2
    return ' '.join(camera_2.class_label_set)

@app.route('/get_class_label_3')
def get_class_label_3():
    global camera_3
    return ' '.join(camera_3.class_label_set)

if __name__ == "__main__":
    app.run(debug=True)
#git 
