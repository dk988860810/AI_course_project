from flask import Flask, request, session, redirect, url_for, render_template ,flash
import mysql.connector
import re 
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'mmm'

# 连接到 MySQL 数据库
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="s22525439",
    database="test"
)

# 用於登錄頁面的路由
@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = conn.cursor(dictionary=True)  # 使用字典游標，以便更容易地訪問結果
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        cursor.close()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = '用戶名/密碼不正確！'

    return render_template('login.html', msg=msg)

# 用於註冊頁面的路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            msg = '帳戶已存在！'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = '無效的電子郵件地址！'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = '用戶名必須只包含字母和數字！'
        elif not username or not password or not email:
            msg = '請填寫表單！'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s ,NULL)', (fullname, username, password, email)) 
            conn.commit()
            msg = '您已成功註冊！'

    elif request.method == 'POST':
        msg = '請填寫表單！'

    return render_template('register.html', msg=msg)

# 首頁路由（只有已登錄的用戶可以訪問）
@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

# 登出路由
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# 用戶資料頁面路由（只有已登錄的用戶可以訪問）
@app.route('/profile')
def profile(): 
    if 'loggedin' in session:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        cursor.close()
        if account:
            # 抓取用戶的頭像路徑
            profile_picture_path = account.get('profile_picture_path', None)
            if profile_picture_path:
                profile_picture_path = profile_picture_path.replace('\\', '/')
                profile_picture_url = url_for('static', filename='profile_pic/' + profile_picture_path)
            else:
                # 如果頭像路徑為None，可以返回一個默認的頭像URL或者一個錯誤消息
                profile_picture_url = url_for('static', filename='profile_pic/none.jpg')
            print(profile_picture_url)
            return render_template('profile.html', account=account, profile_picture_url=profile_picture_url)
    return redirect(url_for('login'))


# 指定上傳照片的目錄
UPLOAD_FOLDER = 'C:/report/try0508/static/profile_pic'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'loggedin' in session:
        # 獲取從表單提交的更新後的個人資料
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # 處理上傳的照片
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file.filename != '':
                 # 將照片保存到指定目錄
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # 只保存檔名到資料庫中
                profile_picture_path = filename
                
        # 執行更新個人資料的 SQL 語句
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts 
            SET fullname = %s, username = %s, password = %s, email = %s , profile_picture_path= %s
            WHERE id = %s
        ''', (fullname, username, password, email, profile_picture_path, session['id']))
        conn.commit()
        cursor.close()
        
        flash('Update success', 'success')
        # 重定向到用戶的個人資料頁面
        return redirect(url_for('profile'))
    else:
        # 如果用戶未登錄，重定向到登錄頁面
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', debug=True)