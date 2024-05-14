from flask import Flask, render_template

app = Flask(__name__)

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 登录页面路由
@app.route('/templates/login.html')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)