# server.py
from flask import Flask, render_template, Response, request, jsonify
import mysql.connector

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



# 接收影像資料流並進行即時播放
@app.route('/video_feed')
def video_feed():
    # 接收來自邊緣計算端的影像資料流
    # 實現即時播放功能
    # ...

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
    app.run(debug=True)