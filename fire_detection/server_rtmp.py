from flask import Flask, render_template, Response, request, jsonify,make_response,url_for,redirect
from flask_socketio import SocketIO, emit
import threading
from queue import Queue, Empty, Full
from datetime import datetime
import mysql.connector
import pickle
import time
import pdfkit
import os
import cv2

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
edge_labels = {}

def frame_processing_thread(edge_id):
    while True:
        frame_stream_queue = frame_stream_queues.get(edge_id, None)
        if not frame_stream_queue:
            time.sleep(1)
            continue

        try:
            frame, class_label_set = frame_stream_queue.get(timeout=1)
            edge_labels[edge_id] = class_label_set
        except Empty:
            continue

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        edge_id, class_label_bytes = pickle.loads(data)
        class_label_set = pickle.loads(class_label_bytes)

        if edge_id not in frame_queues_and_threads:
            frame_stream_queue = Queue(maxsize=30)
            frame_stream_queues[edge_id] = frame_stream_queue

            thread = threading.Thread(target=frame_processing_thread, args=(edge_id,))
            thread.daemon = True
            thread.start()
            frame_queues_and_threads[edge_id] = (frame_stream_queue, thread)

        frame_stream_queue = frame_queues_and_threads[edge_id][0]
        frame_stream_queue.put((None, class_label_set))  # 將 None 作為佔位符,因為我們沒有收到影像資料
    except Exception as e:
        print(f"Error handling video frame: {e}")

def generate_frames(edge_id):
    rtmp_url = f"rtmp://13.214.171.73:{1935+edge_id}/fire{edge_id}/stream_{edge_id}"
    cap = cv2.VideoCapture(rtmp_url)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Directly yield the frame as a JPEG-encoded byte stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')

    cap.release()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/second_floor')
def second_floor():
    return render_template('second_floor.html')

@app.route('/third_floor')
def third_floor():
    return render_template('third_floor.html')
    

@app.route('/video_feed/<int:edge_id>')
def video_feed_route(edge_id):
    if edge_id not in frame_queues_and_threads:
        frame_stream_queue = Queue(maxsize=30)
        frame_stream_queues[edge_id] = frame_stream_queue

        thread = threading.Thread(target=frame_processing_thread, args=(edge_id,))
        thread.daemon = True
        thread.start()
        frame_queues_and_threads[edge_id] = (frame_stream_queue, thread)
    
    return Response(generate_frames(edge_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_class_label')
def get_class_label():
    camera_id = request.args.get('camera_id', type=int)

    if camera_id in edge_labels:
        class_label_set = edge_labels[camera_id]
    else:
        class_label_set = []

    return jsonify(class_label_set)

# 其他路由和函數保持不變
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

@app.route('/table', methods=['GET'])
def table():
    page = request.args.get('page', 1, type=int)
    result = get_data(page=page, per_page=10)
    return render_template('table.html', result=result)

def get_data(page, per_page):
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()

    try:
        offset = (page - 1) * per_page

        count_query = "SELECT COUNT(*) FROM test"
        cursor.execute(count_query)
        total_count = cursor.fetchone()[0]
        total_pages = (total_count + per_page - 1) // per_page  # Calculate total number of pages

        query = "SELECT * FROM test ORDER BY id DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (per_page, offset))
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
            result[0]['total_pages'] = total_pages
            result[0]['current_page'] = page

        return result
    finally:
        cursor.close()
        conn.close()

@app.route('/download_data')
def download():
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    query = "SELECT * FROM users"
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
        <meta charset="UTF-8">
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
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@100..900&display=swap');
        </style>
    </head>
    <body>
    <h1>員工資料</h1>
    <table>
        <tr>
            <th>工號</th>
            <th>姓名</th>
            <th>工作職稱</th>
            <th>所在區域</th>
            <th>打卡時間</th>
            <th>打卡狀態</th>
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
        </tr>
        """

    html += "</table><br><h1>樓層平面圖</h1>"
    count=1
    # 添加图片
    for img in imgs:
        html+=f"<br><h2>{count}樓 平面圖</h2>"
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

@app.route('/redirect')
def reset_clock_status():
    return redirect(url_for('table'))



if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)