import cv2
from ultralytics import YOLO
import socketio
import pickle
import time

# 使用串流模式傳輸影像
def encode_image(img):
    _, encoded_img = cv2.imencode('.jpg', img)
    return encoded_img.tobytes()

# Replace <SERVER_IP> with the IP address of your server
SERVER_IP = '192.168.209.207'
SERVER_PORT = 5000

# Initialize camera and YOLO model
camera = cv2.VideoCapture(0)  # Replace 0 with the appropriate camera index
model = YOLO("model/best.pt")

# Create a SocketIO client instance
sio = socketio.Client()

# Connect to the server
sio.connect(f'http://{SERVER_IP}:{SERVER_PORT}')

@sio.event
def connect():
    print('Connected to the server')

class EdgeComputing:
    def __init__(self, camera, model):
        self.cap = camera
        self.model = model
        self.class_label_set = []
        self.start_time=time.time()
        self.frame_counter = 0
    

    def detect_objects(self, frame, model):
        pre_result_cam = model.predict(frame, verbose=False)
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

    def stream_video(self,edge_id):
        while True:
            success, frame = self.cap.read()
            if success:
                frame_with_detections = self.detect_objects(frame, self.model)
            
                encoded_frame = encode_image(frame_with_detections)
                class_labels_bytes = pickle.dumps(self.class_label_set)

                # Serialize the data
                data = pickle.dumps([edge_id,encoded_frame, class_labels_bytes], protocol=0)

                # Send the serialized data to the server
                sio.emit('video_frame', data)

                self.frame_counter += 1

                current_time = time.time()
                elapsed_time = current_time - self.start_time

                if elapsed_time >= 1.0:  # 每秒執行一次
                    fps = self.frame_counter / elapsed_time
                    print(f"Frames per second: {fps}")
                    self.frame_counter = 0
                    self.start_time = time.time()
                

if __name__ == "__main__":
    
    edge_id=1
    edge_computing = EdgeComputing(camera, model)
    edge_computing.stream_video(edge_id)