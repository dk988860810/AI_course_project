from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
from ultralytics import YOLO
import pickle

app = Flask(__name__)
socketio = SocketIO(app)

class EdgeComputing:
    def __init__(self, camera_index, model_path):
        self.cap = cv2.VideoCapture(camera_index)
        self.class_label_set = []
        self.model = YOLO("model/best.pt")

    def detect_objects(self, frame, model):
        pre_result_cam = model.predict(frame,verbose=False)
        self.class_label_set = []
        for data in pre_result_cam[0].boxes:
            x1, y1, x2, y2 = data.xyxy[0]
            class_id = int(data.cls)
            class_label = pre_result_cam[0].names[class_id]
            class_conf = "{:.2f}".format(float(data.conf))
            if data.conf >= 0.5:
                #self.class_label_set.append(f'{class_label} {class_conf}')
                self.class_label_set.append(f'{class_label}')
                org = (int(x1), int(y1))
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                color = (255, 0, 0)
                thickness = 2
                output_text = f'{class_label} {class_conf}'
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 3)
                cv2.putText(frame, output_text, org, font, fontScale, color, thickness)
        return frame  # Replace with your processed frame

    def stream_video(self):
        while True:
            success, frame = self.cap.read()
            if success:
                frame_with_detections = self.detect_objects(frame,self.model)
                frame_encoded = cv2.imencode('.jpg', frame_with_detections)[1].tobytes()
                class_label_bytes = pickle.dumps(self.class_label_set, protocol=2).decode('latin1')
                data_to_send = pickle.dumps((frame_encoded, class_label_bytes), protocol=2)
                socketio.emit('video_frame', data_to_send, namespace='/video_feed_1')
                print('image_send')

@socketio.on('connect', namespace='/video_feed_1')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/video_feed_1')
def handle_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    edge_computing = EdgeComputing(camera_index=0, model_path="model/best.pt")
    edge_computing.stream_video()
    socketio.run(app)
