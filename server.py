from flask import Flask, render_template, Response, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import threading
from queue import Queue, Empty, Full
from datetime import datetime
import mysql.connector
import pickle
import time
from PIL import Image
import io

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

frame_queues_and_threads = {}
frame_stream_queues = {}

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        edge_id, frame_encoded, class_label_bytes = pickle.loads(data)
        class_label_set = pickle.loads(class_label_bytes)
        print(f"Received data from edge {edge_id}")

        if edge_id not in frame_queues_and_threads:
            frame_stream_queue = Queue(maxsize=10)
            frame_queues_and_threads[edge_id] = frame_stream_queue
            frame_stream_queues[edge_id] = frame_stream_queue
            print(f"Created stream queue for edge {edge_id}")

        frame_stream_queue = frame_queues_and_threads[edge_id]
        frame_stream_queue.put((frame_encoded, class_label_set), timeout=1)
        print(f"Added frame to stream queue for edge {edge_id}")
    except Full:
        print(f"Stream queue for edge {edge_id} is full, skipping frame")
    except Exception as e:
        print(f"Error handling video frame: {e}")

def generate_frames(edge_id):
    while True:
        frame_stream_queue = frame_stream_queues.get(edge_id, None)
        if not frame_stream_queue:
            print(f"No stream queue found for edge {edge_id}")
            time.sleep(1)
            continue

        try:
            frame_encoded, class_label_set = frame_stream_queue.get(timeout=1)
            print(f"Yielding frame bytes for edge {edge_id}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded + b'\r\n')
        except Empty:
            print(f"Stream queue for edge {edge_id} is empty, waiting for frames")
            time.sleep(0.1)
            continue

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_1')
def video_feed_route_1():
    return Response(generate_frames(1), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/video_feed_2')
# def video_feed_route_2():
#     return Response(generate_frames(2), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/video_feed_3')
# def video_feed_route_3():
#     return Response(generate_frames(3), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_class_label')
def get_class_label():
    camera_id = request.args.get('camera_id', type=int)
    class_label_set = []

    if camera_id in frame_queues_and_threads:
        frame_queue, _ = frame_queues_and_threads[camera_id]
        if frame_queue is not None and not frame_queue.empty():
            frame, labels = frame_queue.get()
            class_label_set = labels

    return ' '.join(class_label_set)

@app.route('/submit_data', methods=['POST'])
def submit():
    if request.method == 'POST':
        data = request.get_json()
        floor = data['floor']
        area = data['area']
        cancel_reason = data['cancel_reason']
        situation = data['situation']

        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor()

        current_date = datetime.now().date()
        current_time = datetime.now().time()

        insert_query = "INSERT INTO test (date, time, floor, area, cancel_reason, situation) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (current_date, current_time, floor, area, cancel_reason, situation))

        conn.commit()
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
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * 20

        count_query = "SELECT COUNT(*) FROM test"
        cursor.execute(count_query)
        total_count = cursor.fetchone()[0]

        query = "SELECT * FROM test ORDER BY id DESC LIMIT 20 OFFSET %s"
        cursor.execute(query, (offset,))
        data = cursor.fetchall()

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
