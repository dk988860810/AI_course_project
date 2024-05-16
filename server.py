from flask import Flask, render_template, Response, request, jsonify,make_response,url_for
from flask_socketio import SocketIO, emit
import threading
from queue import Queue, Empty, Full
from datetime import datetime
import mysql.connector
import pickle
import time
import pdfkit
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

mysql_config = {
    'host': '54.162.189.102',
    'port': '3306',
    'user': 'test_user',
    'password': 'testpassword',
    'database': 'aws_test'
}

frame_queues_and_threads = {}
frame_stream_queues = {}

def frame_processing_thread(edge_id):
    while True:
        frame_stream_queue = frame_stream_queues.get(edge_id, None)
        if not frame_stream_queue:
            # print(f"No stream queue found for edge {edge_id}")
            time.sleep(1)
            continue

        try:
            frame_encoded, class_label_set = frame_stream_queue.get(timeout=1)
            # print(f"Processing frame for edge {edge_id}")
            # Process frame here if needed
        except Empty:
            # print(f"Stream queue for edge {edge_id} is empty, waiting for frames")
            time.sleep(0.1)
            continue

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        edge_id, frame_encoded, class_label_bytes = pickle.loads(data)
        class_label_set = pickle.loads(class_label_bytes)
        # print(f"Received data from edge {edge_id}")

        if edge_id not in frame_queues_and_threads:
            frame_stream_queue = Queue(maxsize=30)
            frame_stream_queues[edge_id] = frame_stream_queue
            # print(f"Created stream queue for edge {edge_id}")

            thread = threading.Thread(target=frame_processing_thread, args=(edge_id,))
            thread.daemon = True
            thread.start()
            frame_queues_and_threads[edge_id] = (frame_stream_queue, thread)
            # print(f"Started processing thread for edge {edge_id}")

        frame_stream_queue = frame_queues_and_threads[edge_id][0]
        frame_stream_queue.put((frame_encoded, class_label_set), timeout=1)
        # print(f"Added frame to stream queue for edge {edge_id}")
    except Full:
         print(f"Stream queue for edge {edge_id} is full, skipping frame")
    except Exception as e:
         print(f"Error handling video frame: {e}")

def generate_frames(edge_id):
    while True:
        frame_stream_queue = frame_stream_queues.get(edge_id, None)
        if not frame_stream_queue:
            # print(f"No stream queue found for edge {edge_id}")
            time.sleep(1)
            continue

        try:
            frame_encoded, class_label_set = frame_stream_queue.get(timeout=1)
            # print(f"Yielding frame bytes for edge {edge_id}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded + b'\r\n')
        except Empty:
            # print(f"Stream queue for edge {edge_id} is empty, waiting for frames")
            time.sleep(0.1)
            continue


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_1')
def video_feed_route_1():
    return Response(generate_frames(1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_2')
def video_feed_route_2():
    return Response(generate_frames(2), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app.route('/video_feed_3')
# def video_feed_route_3():
#     return Response(generate_frames(3), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_class_label')
def get_class_label():
    camera_id = request.args.get('camera_id', type=int)
    class_label_set = []

    if camera_id in frame_queues_and_threads:
        frame_queue = frame_queues_and_threads[camera_id][0]
        if frame_queue is not None and not frame_queue.empty():
            _, labels = frame_queue.get()
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

@app.route('/download_data')
def download():
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    query = "SELECT * FROM employees"
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    img_folder_path = os.path.join("static", "img","floorplan")
    imgs = os.listdir(img_folder_path)
    
    # 创建表格头部
    html = """
    <html>
    <head>
        <style>
            table, th, td {
                border: 1px solid black;
                border-collapse: collapse;
                padding: 5px;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
    <h1>Employee Data</h1>
    <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Job Title</th>
            <th>Department</th>
            <th>Office Location</th>
            <th>Phone Number</th>
            <th>Emergency Contact</th>
        </tr>
    """
    
    # 填充表格数据
    for row in result:
        html += f"""
        <tr>
            <td>{row[0]}</td>
            <td>{row[1]}</td>
            <td>{row[2]}</td>
            <td>{row[3]}</td>
            <td>{row[4]}</td>
            <td>{row[5]}</td>
            <td>{row[6]}</td>
        </tr>
        """

    html += "</table><br><h1>Floor Plan</h1>"
    count=1
    # 添加图片
    for img in imgs:
        html+=f"<br><h2>{count} Floor</h2>"
        img_url = url_for('static', filename=f'img/floorplan/{img}', _external=True)
        html += f"<img src='{img_url}' style='max-width:100%;height:auto;'><br>"
        count+=1
        
    html += "</body></html>"
    
    try:
        pdf = pdfkit.from_string(html, False, configuration=config)
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "attachment; filename=data.pdf"
        return response
    except IOError as e:
        print("wkhtmltopdf reported an error:", e)
        return str(e), 500



if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
