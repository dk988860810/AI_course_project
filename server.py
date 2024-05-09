from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
from threading import Thread
from queue import Queue
from datetime import datetime
import mysql.connector
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

mysql_config = {
    'host': '127.0.0.1',
    'port': '3306',
    'user': 'root',
    'password': 'ccps971304',
    'database': 'AI_course'
}

current_datetime = datetime.now()
formatted_date = current_datetime.strftime("%Y-%m-%d")
formatted_time = current_datetime.strftime("%H-%M-%S")

# Create separate queues for each camera
frame_queues = {
    1: Queue(),
    2: Queue(),
    3: Queue()
}

# Function to handle the received frames and labels
@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        edge_id, frame_encoded, class_label_bytes = pickle.loads(data)
        class_label_set = pickle.loads(class_label_bytes)

        # Decode the frame
        frame = cv2.imdecode(np.frombuffer(frame_encoded, np.uint8), cv2.IMREAD_COLOR)

        # Add the frame and labels to the respective queue
        frame_queues[edge_id].put((frame, class_label_set))
    except Exception as e:
        print(f"Error handling video frame: {e}")

# Function to generate frames for streaming
def generate_frames(camera_id):
    frame_queue = frame_queues[camera_id]

    while True:
        if not frame_queue.empty():
            frame, class_label_set = frame_queue.get()
            print(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_1')
def video_feed_route_1():
    return Response(generate_frames(1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_2')
def video_feed_route_2():
    return Response(generate_frames(2), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_3')
def video_feed_route_3():
    return Response(generate_frames(3), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_class_label')
def get_class_label():
    
    camera_id = request.args.get('camera_id', type=int)
    class_label_set = []

    if camera_id in frame_queues:
        frame, labels = frame_queues[camera_id].get()
        class_label_set = labels
    else:
        return ''

    return ' '.join(class_label_set)

@app.route('/submit_data',methods=['POST'])
def submit():
    if request.method == 'POST':
        data = request.get_json()
        floor = data['floor']
        area = data['area']
        cancel_reason = data['cancel_reason']
        situation = data['situation']
        
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()
        
        # 獲取當前日期和時間
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        
        insert_query = "INSERT INTO test (date, time, floor, area, cancel_reason, situation) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (current_date, current_time, floor, area, cancel_reason, situation))
        
        conn.commit()
        
        # 關閉資料庫連接
        cursor.close()
        conn.close()
        
        return '資料已成功提交到資料庫！'

@app.route('/table')
def table():
    return render_template('table.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    try:
        # 獲取查詢參數,例如頁碼
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * 20  # 每頁20筆資料,計算起始位置

        # 獲取總數據條目數
        count_query = "SELECT COUNT(*) FROM test"
        cursor.execute(count_query)
        total_count = cursor.fetchone()[0]

        # 從資料庫獲取資料
        query = "SELECT * FROM test ORDER BY id DESC LIMIT 20 OFFSET %s"
        cursor.execute(query, (offset,))
        data = cursor.fetchall()

        # 將資料轉換為JSON格式
        result = []
        for row in data:
            result.append({
                'id': row[0],
                'date': row[1].isoformat(),
                'time': row[2].strftime('%H:%M:%S') if isinstance(row[2], datetime) else str(row[2]),
                'floor': row[3],
                'area': row[4],
                'cancel_reason': row[5],
                'situation': row[6]
            })

        if result:
            result[0]['total_count'] = total_count

        return jsonify(result)

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    socketio.run(app, host='localhost',port=5000, debug=True)