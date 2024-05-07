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

# 顯示資料庫資料
@app.route('/table')
def table():
    # 渲染顯示資料庫資料的模板
    # ...

@app.route('/get_data', methods=['GET'])
def get_data():
    # 從資料庫獲取資料
    # 返回 JSON 格式的資料
    # ...

if __name__ == "__main__":
    app.run(debug=True)