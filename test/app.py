from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user

app = Flask(__name__)
app.secret_key = 'abc'

# MySQL configurations
app.config['MYSQL_HOST'] = '54.162.189.102'
app.config['MYSQL_USER'] = 'test_user'
app.config['MYSQL_PASSWORD'] = 'testpassword'
app.config['MYSQL_DB'] = 'aws_test'

mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM test_accounts WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(int(user[0]), user[1], user[3])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO test_accounts (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
            mysql.connection.commit()
            cursor.close()
            flash('Registered successfully!', 'success')
        except Exception as e:
            cursor.close()
            flash(str(e), 'danger')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM test_accounts WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        if user and user[2] == password:  # 检查明文密码
            login_user(User(int(user[0]), user[1], user[3]))
            if user[3] == 'HR':
                return redirect(url_for('HR'))
            elif user[3] == 'police':
                return redirect(url_for('police'))
            elif user[3] == 'fire':
                return redirect(url_for('fire'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/HR')
@login_required
def HR():
    if current_user.role != 'HR':
        return redirect(url_for('login'))
    return render_template('HR.html')

@app.route('/police')
@login_required
def police():
    if current_user.role != 'police':
        return redirect(url_for('login'))
    return render_template('police.html')

@app.route('/fire')
@login_required
def fire():
    if current_user.role != 'fire':
        return redirect(url_for('login'))
    return render_template('fire.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
