from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

# Initialize the camera
camera = cv2.VideoCapture(0)  # Use 0 for web camera

def generate_frames():
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()
        if not success:
            break
        else:
            # Draw a rectangle on the frame
            start_point = (50, 50)
            end_point = (300, 300)
            color = (255, 0, 0)  # Blue color in BGR
            thickness = 2

            frame = cv2.rectangle(frame, start_point, end_point, color, thickness)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Concatenate frame one by one and show result
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500)
