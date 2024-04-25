from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from flask import render_template

app = Flask(__name__, template_folder='C:/Users/hsu/OneDrive/桌面/report/登录')

# 连接到 MySQL 数据库
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="asd8955775",
    database="report"
)

# 路由处理注册页面
@app.route('/')
def register_page():
    return render_template('signup.html')

# 路由处理注册请求
@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    jobtitle = request.form['jobtitle']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    
    cursor = conn.cursor()
    # 在数据库中插入新用户
    cursor.execute("INSERT INTO users (name ,jobtitle ,email ,phone, password) VALUES (%s, %s ,%s, %s,%s)", (name, jobtitle ,email ,phone,password))
    conn.commit()
    
    return redirect(url_for('success'))

# 注册成功页面
@app.route('/success')
def success():
    return "Registration successful!"

if __name__ == '__main__':
    app.run(debug=True)
#test git