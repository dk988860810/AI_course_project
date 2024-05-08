# server.py
from flask import Flask, render_template, Response, request , jsonify
import socket
import pickle
from datetime import datetime
from threading import Thread
import mysql.connector
import json

# Flask 設置和路由
# ...
app = Flask(__name__)

mysql_config={
    'host': '127.0.0.1',
    'port': '3306',
    'user': 'root',
    'password': 'ccps971304',
    'database': 'AI_course'
}

current_datetime = datetime.now()
formatted_date = current_datetime.strftime("%Y-%m-%d")
formatted_time = current_datetime.strftime("%H-%M-%S")

connections = {}

def handle_connection(conn, addr):
    print(f'Handling connection from {addr}')
    try:
        while True:
            data = conn.recv(1024 * 1024)  # 接收資料
            if not data:
                break

            print(f'Received data: {data}')

            # 解碼資料
            try:
    # Your code that might raise the exception
                frame, class_label_bytes = pickle.loads(data, encoding='latin1')
            except pickle.UnpicklingError as e:
    # Handle the exception
                print("An error occurred while unpickling:", e)
    # Optionally, you can provide default values or take alternative actions here
            # 使用 Pickle 解碼 class_label_bytes
            class_label_set = pickle.loads(class_label_bytes.encode('latin1'))
            # 在這裡處理接收到的影像資料流和 class_label_set
            # 例如，將影像資料流和 class_label_set 存儲在 connections 字典中
            connections[addr] = (frame, class_label_set)

    finally:
        conn.close()
        print(f'Connection from {addr} closed')



def stream_video():
    while True:
        frames = []
        for addr, (frame, class_label_set) in connections.items():
            frames.append(frame)
            # 在這裡處理 class_label_set
            print(f'Labels from {addr}: {class_label_set}')

        if frames:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + b''.join(frames) + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_1')
def video_feed_1():
    return Response(stream_video(1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_2')
def video_feed_2():
    return Response(stream_video(2), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_3')
def video_feed_3():
    return Response(stream_video(3), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_class_label')
def get_class_label():
    camera_id = request.args.get('camera_id', type=int)
    class_label_set = []
    
    for addr, (frame, labels) in connections.items():
        if addr in devices[camera_id]:
            class_label_set = labels
            break

    return jsonify(list(class_label_set))

# 處理用戶介面資料並存儲到資料庫
@app.route('/submit_data', methods=['POST'])
def submit_data():
    # 獲取用戶輸入資料
    # 存儲到 MySQL 資料庫
    # ...
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
    

# 顯示資料庫資料
@app.route('/table')
def table():
    # 渲染顯示資料庫資料的模板
    # ...
    return render_template('table.html')


@app.route('/get_data', methods=['GET'])
def get_data():
    # 從資料庫獲取資料
    # 返回 JSON 格式的資料
    # ...
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
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 8000))
    server_socket.listen(5)
    print('Server is listening on 127.0.0.1:8000')

    while True:
        conn, addr = server_socket.accept()
        thread = Thread(target=handle_connection, args=(conn, addr))
        thread.start()

    server_socket.close()