from flask import Flask, render_template

app = Flask(__name__)

# 主頁面路由
@app.route('/')
def index():
    return render_template('home.html')

# 登入頁面路由
@app.route('/templates/login.html')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)