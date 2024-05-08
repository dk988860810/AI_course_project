from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import pickle
from datetime import datetime
from threading import Thread
import mysql.connector

app = Flask(__name__)
socketio = SocketIO(app)

mysql_config = {
    'host': '127.0.0.1',
    'port': '3306',
    'user': 'root',
    'password': 'ccps971304',
    'database': 'AI_course'
}

connections = {}

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

def handle_connection(data):
    frame, class_label_bytes, addr = data
    try:
        frame = pickle.loads(frame)
        class_label_set = pickle.loads(class_label_bytes.encode('latin1'))
        connections[addr] = (frame, class_label_set)
        print(f'Connection from {addr} handled')
    except pickle.UnpicklingError as e:
        print("An error occurred while unpickling:", e)

def stream_video():
    while True:
        socketio.sleep(0.1)  # Adjust sleep time as needed
        for addr, (frame, class_label_set) in connections.items():
            emit('video_frame', {'frame': frame, 'labels': class_label_set}, room=addr)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('get_class_label')
def get_class_label(camera_id):
    class_label_set = []

    for addr, (_, labels) in connections.items():
        if addr == camera_id:
            class_label_set = labels
            break

    emit('class_labels', {'labels': list(class_label_set)}, room=request.sid)

@app.route('/submit_data', methods=['POST'])
def submit_data():
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
        
        return 'Data successfully submitted to the database!'

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
    socketio.start_background_task(stream_video)
    socketio.run(app)
