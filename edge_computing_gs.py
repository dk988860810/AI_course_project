import cv2
from ultralytics import YOLO
import socketio
import pickle
import subprocess

# Replace <SERVER_IP> with the IP address of your server
SERVER_IP = '192.168.8.150'
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
        while True:
            success, frame = self.cap.read()
            if success:
                frame_with_detections = self.detect_objects(frame, self.model)

                # 构建 GStreamer 管道命令
                gst_pipeline = f"gst-launch-1.0 appsrc ! videoconvert ! x264enc tune=zerolatency ! rtph264pay ! gdppay ! tcpserversink host={SERVER_IP} port=8554"

                # 启动 GStreamer 管道
                gst_process = subprocess.Popen(gst_pipeline, shell=True, stdin=subprocess.PIPE)

                # 将帧写入 GStreamer 管道
                gst_process.stdin.write(cv2.imencode('.jpg', frame_with_detections)[1].tobytes())

                # Serialize the class labels
                class_labels_bytes = pickle.dumps(self.class_label_set)

                # Send the serialized class labels to the server
                data = pickle.dumps([edge_id, class_labels_bytes], protocol=0)
                sio.emit('video_frame', data)

        # Clean up the GStreamer pipeline
        gst_process.stdin.close()
        gst_process.terminate()
        gst_process.wait()

if __name__ == "__main__":
    edge_id = 1
    edge_computing = EdgeComputing(camera, model)
    edge_computing.stream_video(edge_id)