from flask import Flask, render_template, Response, request , jsonify
import cv2
from threading import Thread
from queue import Queue
from ultralytics import YOLO
from datetime import datetime
import mysql.connector

mysql_config={
    'host': '127.0.0.1',
    'port': '3306',
    'user': 'root',
    'password': 'ccps971304',
    'database': 'AI_course'
}

app = Flask(__name__)
current_datetime = datetime.now()
formatted_date = current_datetime.strftime("%Y-%m-%d")
formatted_time = current_datetime.strftime("%H-%M-%S")

class Camera:
    def __init__(self, camera_index):
        self.cap = cv2.VideoCapture(camera_index)
        self.frame_queue = Queue()
        self.class_label_set = []
        self.model = YOLO("model/best.pt")

    def detect_objects(self, frame, model):
        pre_result_cam = model.predict(frame,verbose=False)
        self.class_label_set = []
        for data in pre_result_cam[0].boxes:
            x1, y1, x2, y2 = data.xyxy[0]
            class_id = int(data.cls)
            class_label = pre_result_cam[0].names[class_id]
            class_conf = "{:.2f}".format(float(data.conf))
            if data.conf >= 0.5:
                #self.class_label_set.append(f'{class_label} {class_conf}')
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
    
    def video_feed_and_save(self, camera_id=None):
        def detect_and_save():

            path="C:/Users/dk988/Desktop/AI_project_video/camera_"+str(camera_id)
            file_name = "{}/{}_{}.avi".format(path,formatted_date,formatted_time)
            #-----影片存檔----
            # fourcc = cv2.VideoWriter_fourcc(*'XVID')
            # out = cv2.VideoWriter(file_name, fourcc, 30.0, (640, 480))

            # try:
            #     while True:
            #         success, frame = self.cap.read()
        
            #         if not success:
            #             frame=cv2.imread("static/icon.jpg")
            #             self.frame_queue.put(frame)
            #         else:
            #             self.class_label_set = []
            #             frame = self.detect_objects(frame, self.model)
            #             out.write(frame)
            #             self.frame_queue.put(frame)
            # finally:
            #     out.release()
            #-----影片不存檔----
            while True:
                    success, frame = self.cap.read()
        
                    if not success:
                        frame=cv2.imread("static/icon.jpg")
                        self.frame_queue.put(frame)
                    else:
                        self.class_label_set = []
                        frame = self.detect_objects(frame, self.model)
                        #out.write(frame)
                        self.frame_queue.put(frame)
            #-------------------
        t = Thread(target=detect_and_save)
        t.start()

    def generate_frames(self):
        while True:
            frame = self.frame_queue.get()
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


camera_1 = Camera(1)  # First camera
camera_2 = Camera(3)  # Second camera
camera_3 = Camera(2)  # Third camera

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed_1')
def video_feed_route_1():
    camera_1.video_feed_and_save(camera_id=1)
    return Response(camera_1.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_2')
def video_feed_route_2():
    camera_2.video_feed_and_save(camera_id=2)
    return Response(camera_2.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_3')
def video_feed_route_3():
    camera_3.video_feed_and_save(camera_id=3)
    return Response(camera_3.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_class_label')
def get_class_label():
    camera_id = request.args.get('camera_id', type=int)

    if camera_id == 1:
        class_label_set = camera_1.class_label_set
    elif camera_id == 2:
        class_label_set = camera_2.class_label_set
    elif camera_id == 3:
        class_label_set = camera_3.class_label_set
    else:
        # 如果提供了无效的摄像头 ID，则返回空字符串或其他适当的响应
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
    app.run(debug=True)

