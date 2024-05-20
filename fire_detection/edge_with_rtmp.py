import cv2
from ultralytics import YOLO
import socketio
import pickle
import time
import threading
import subprocess
from queue import Queue
import queue

# Replace <SERVER_IP> with the IP address of your server
SERVER_IP = '172.17.244.11'
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
        self.stop_event = threading.Event()
        self.frame_queue = Queue(maxsize=10)  # 限制隊列大小
        self.rtmp_thread = threading.Thread(target=self.run_rtmp)
        self.rtmp_thread.start()
        self.edge_id = edge_id

    def run_rtmp(self):
        rtmp_url = "rtmp://13.214.171.73/live/stream_1"
        rtmp_command = [
            "ffmpeg",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", "640x480",
            "-r", "30",
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-f", "flv",
            rtmp_url
        ]
        self.rtmp_process = subprocess.Popen(rtmp_command, stdin=subprocess.PIPE)

        while not self.stop_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)
            except queue.Empty:
                continue
            else:
                print("Writing frame to FFmpeg process")
                self.rtmp_process.stdin.write(frame.tobytes())

        self.rtmp_process.stdin.close()
        self.rtmp_process.wait()

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

    def stream_video(self, edge_id):
        try:
            while not self.stop_event.is_set():
                success, frame = self.cap.read()
                if success:
                    #frame_with_detections = self.detect_objects(frame, self.model)
                    self.frame_queue.put(frame)

                    class_labels_bytes = pickle.dumps(self.class_label_set)
                    data = pickle.dumps([self.edge_id, class_labels_bytes], protocol=0)
                    sio.emit('video_frame', data)

                    self.frame_counter += 1

                    current_time = time.time()
                    elapsed_time = current_time - self.start_time

                    if elapsed_time >= 1.0:
                        fps = self.frame_counter / elapsed_time
                        print(f"Frames per second: {fps}")
                        self.frame_counter = 0
                        self.start_time = time.time()
        except KeyboardInterrupt:
            print("Keyboard Interrupt received, stopping...")
            self.stop_event.set()
            self.rtmp_thread.join()

if __name__ == "__main__":
    edge_id = 1
    edge_computing = EdgeComputing(camera, model)
    stream_thread = threading.Thread(target=edge_computing.stream_video, args=(edge_id,))
    stream_thread.start()

    # 保持主線程運行，同時允許處理其他事件
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Main thread Keyboard Interrupt received, stopping...")
        edge_computing.stop_event.set()  # 設置事件對象以通知線程終止
        edge_computing.rtmp_thread.join()  # 等待RTMP線程完成
        stream_thread.join()  # 等待串流線程完成
        camera.release()
        sio.disconnect()
