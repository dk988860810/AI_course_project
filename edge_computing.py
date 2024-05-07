# edge_computing.py
import cv2
from ultralytics import YOLO
import socket
import pickle

class EdgeComputing:
    def __init__(self, camera_index):
        self.cap = cv2.VideoCapture(camera_index)
        self.model = YOLO("model/best.pt")
        self.class_label_set = []
        self.server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)


    def detect_objects(self, frame, model):
        # 使用 YOLO 模型進行物體檢測
        # ...
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
        return frame

    def stream_video(self):
        while True:
            success, frame = self.cap.read()
            if success:
                frame_with_detections = self.detect_objects(frame)
                # 將檢測到的影像資料流傳送到伺服器端
                frame_encoded = cv2.imencode('.jpg', frame_with_detections)[1].tobytes()
                data_to_send = pickle.dumps((frame_encoded, self.class_label_set))
                
                self.server_socket.sendall(data_to_send)

            else:
                break

if __name__ == "__main__":
    edge_computing = EdgeComputing(camera_index=0,server_ip='localhost',server_port=8000)
    edge_computing.stream_video()