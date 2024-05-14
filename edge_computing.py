import cv2
from ultralytics import YOLO
import socketio
import pickle
import time
import threading
from queue import Queue

# 使用串流模式傳輸影像
def encode_image(img):
    _, encoded_img = cv2.imencode('.jpg', img)
    return encoded_img.tobytes()

# Replace <SERVER_IP> with the IP address of your server
<<<<<<< HEAD
SERVER_IP = '172.17.244.4'
=======
SERVER_IP = '192.168.8.150'
>>>>>>> 04301db27345072d1e9e3a259829ce3563ec4d79
SERVER_PORT = 5000

# Initialize camera and YOLO model
camera = cv2.VideoCapture('testvideo.mp4')  # Replace 0 with the appropriate camera index
model = YOLO("model/best.pt")

# Create a SocketIO client instance
sio = socketio.Client()

# Connect to the server
sio.connect(f'http://{SERVER_IP}:{SERVER_PORT}')

@sio.event
def connect():
    print('Connected to the server')

@sio.event
def disconnect():
    print('Disconnected from the server')

class EdgeComputing:
    def __init__(self, camera, model):
        self.cap = camera
        self.model = model
        self.class_label_set = []
        self.start_time = time.time()
        self.frame_counter = 0
        self.encode_queue = Queue()
        self.stop_event = threading.Event()  # 創建一個事件對象
        self.encode_thread = threading.Thread(target=self.encode_frames)
        self.encode_thread.start()

    def encode_frames(self):
        while not self.stop_event.is_set():  # 檢查事件是否設置
            print('encoding')

            success, frame = self.cap.read()
            if success:
                frame_with_detections = self.detect_objects(frame, self.model)
                encoded_frame = encode_image(frame_with_detections)
                class_labels_bytes = pickle.dumps(self.class_label_set)
                data = pickle.dumps([1, encoded_frame, class_labels_bytes], protocol=0)
                self.encode_queue.put(data)

    def detect_objects(self, frame, model):
        print("detecting")
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

    def stream_video(self, edge_id):
        try:
            while True:
                print("streaming")
                if not self.encode_queue.empty():
                    data = self.encode_queue.get()
                    sio.emit('video_frame', data)

                    self.frame_counter += 1

                    current_time = time.time()
                    elapsed_time = current_time - self.start_time

                    if elapsed_time >= 1.0:  # 每秒執行一次
                        fps = self.frame_counter / elapsed_time
                        print(f"Frames per second: {fps}")
                        self.frame_counter = 0
                        self.start_time = time.time()
        except KeyboardInterrupt:
            print("Keyboard Interrupt received, stopping...")
            self.stop_event.set()  # 設置事件對象以通知線程終止
            self.encode_thread.join()  # 等待線程完成

if __name__ == "__main__":
    edge_id = 1
    edge_computing = EdgeComputing(camera, model)
    edge_computing.stream_video(edge_id)

    # 添加無限迴圈以保持主線程運行
    while True:
        pass