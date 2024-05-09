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

# 創建一個字典來存儲每個邊緣設備的獨立佇列和線程
frame_queues_and_threads = {}

# 函數來處理收到的影像框架和標籤
@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        edge_id, frame_encoded, class_label_bytes = pickle.loads(data)
        class_label_set = pickle.loads(class_label_bytes)
        print(f"Received data from edge {edge_id}")
        # 解碼影像框架
        frame = cv2.imdecode(np.frombuffer(frame_encoded, np.uint8), cv2.IMREAD_COLOR)
        # 為該邊緣設備創建一個獨立的佇列和線程(如果不存在)
        if edge_id not in frame_queues_and_threads:
            frame_queue = Queue()
            frame_queues_and_threads[edge_id] = (frame_queue, None)

        # 獲取該設備的佇列
        frame_queue, _ = frame_queues_and_threads[edge_id]

        # 將影像框架和標籤添加到佇列
        if frame_queue is not None:
            frame_queue.put((frame, class_label_set))
    except Exception as e:
        print(f"Error handling video frame: {e}")

# 生成影像框架的工作線程
def worker(edge_id, frame_queue, frame_stream_queue):
    while True:
        if not frame_queue.empty():
            frame, class_label_set = frame_queue.get()
            print(f"Dequeued frame from edge {edge_id}")
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            frame_stream_queue.put(frame_bytes)
            print(f"Added frame bytes to stream queue for edge {edge_id}")


def generate_frames(edge_id):
    frame_queue, thread = frame_queues_and_threads.get(edge_id, (None, None))
    frame_stream_queue = Queue()

    if frame_queue is None:
        # 創建一個新的佇列
        frame_queue = Queue()
        frame_queues_and_threads[edge_id] = (frame_queue, None)

    if thread is None:
        # 創建一個新的線程來運行 worker 函數
        thread = Thread(target=worker, args=(edge_id, frame_queue, frame_stream_queue))
        thread.daemon = True
        thread.start()
        frame_queues_and_threads[edge_id] = (frame_queue, thread)

    # 從 frame_stream_queue 獲取生成的影像框架
    while True:
        if not frame_stream_queue.empty():
            frame_bytes = frame_stream_queue.get()
            print(f"Yielding frame bytes for edge {edge_id}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
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

    if camera_id in frame_queues_and_threads:
        frame_queue, labels = frame_queues_and_threads[camera_id]
        if frame_queue is not None and not frame_queue.empty():
            frame, labels = frame_queue.get()
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
    socketio.run(app, host='0.0.0.0',port=5000, debug=True)