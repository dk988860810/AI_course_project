from flask import Flask, render_template, request, Response
import cv2
import numpy as np
import base64

app = Flask(__name__)

def process_image(frame):
    # 在图像上添加一个矩形框
    # 这里只是简单地在图像中心添加一个红色的矩形框
    height, width, _ = frame.shape
    cv2.rectangle(frame, (width // 4, height // 4), (3 * width // 4, 3 * height // 4), (0, 0, 255), 3)
    return frame

def gen(camera):
    while True:
        success, frame = camera.read()
        if not success:
            break
        frame = process_image(frame)
        # 将图像编码为base64字符串
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # 使用摄像头0，你也可以更改为其他摄像头
    camera = cv2.VideoCapture(0)
    return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
