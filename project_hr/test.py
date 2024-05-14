from flask import Flask, render_template
import mysql.connector

app = Flask(__name__, static_url_path='/static')

@app.route('/test.py')
def test():
    return render_template('HR.html')

@app.route('/')
def index():
    # 创建连接
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="zzymx.1219",
        database="test_schema",
        auth_plugin='mysql_native_password'
    )

    # 创建游标对象
    mycursor = mydb.cursor()

    # 执行 SQL 查询
    mycursor.execute("SELECT * FROM employees")

    # 获取结果
    myresult = mycursor.fetchall()

    # 关闭连接
    mydb.close()

    return render_template('HR.html', rows=myresult)


if __name__ == '__main__':
    app.run(debug=True)


# from flask import Flask, render_template, request, jsonify
# from werkzeug.utils import secure_filename
# import os
# import mysql.connector

# app = Flask(__name__, static_url_path='/static')
# app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# # 创建数据库连接
# mydb = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="zzymx.1219",
#     database="test_schema",
#     auth_plugin='mysql_native_password'
# )

# # 创建游标对象
# mycursor = mydb.cursor()

# # 主页路由
# @app.route('/')
# def index():
#     mycursor.execute("SELECT * FROM employees")
#     employees = mycursor.fetchall()
#     return render_template('HR.html', employees=employees)

# # 获取员工数据路由
# @app.route('/get_employee/<int:employee_id>', methods=['GET'])
# def get_employee(employee_id):
#     mycursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
#     employee = mycursor.fetchone()
#     if employee:
#         employee_dict = {
#             'employee_id': employee[0],
#             'name': employee[1],
#             'job_title': employee[2],
#             'department': employee[3],
#             'location': employee[4],
#             'phone': employee[5],
#             'emergency_contact': employee[6],
#             'personal_files': employee[7]
#         }
#         return jsonify(employee_dict)
#     else:
#         return jsonify({'error': 'Employee not found'}), 404

# # 添加员工路由
# @app.route('/add_employee', methods=['POST'])
# def add_employee():
#     name = request.form['name']
#     job_title = request.form['jobTitle']
#     department = request.form['department']
#     location = request.form['location']
#     phone = request.form['phone']
#     emergency_contact = request.form['emergencyContact']
#     personal_files = request.files.getlist('personalFiles')

#     file_paths = []
#     for file in personal_files:
#         if file.filename != '':
#             filename = secure_filename(file.filename)
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(file_path)
#             file_paths.append(file_path)

#     personal_files_str = ','.join(file_paths)

#     sql = "INSERT INTO employees (name, job_title, department, location, phone, emergency_contact, personal_files) VALUES (%s, %s, %s, %s, %s, %s, %s)"
#     values = (name, job_title, department, location, phone, emergency_contact, personal_files_str)
#     mycursor.execute(sql, values)
#     mydb.commit()

#     return 'Employee added successfully'

# # 更新员工路由
# @app.route('/update_employee', methods=['POST'])
# def update_employee():
#     employee_id = request.form['employeeId']
#     name = request.form['name']
#     job_title = request.form['jobTitle']
#     department = request.form['department']
#     location = request.form['location']
#     phone = request.form['phone']
#     emergency_contact = request.form['emergencyContact']

#     sql = "UPDATE employees SET name = %s, job_title = %s, department = %s, location = %s, phone = %s, emergency_contact = %s WHERE employee_id = %s"
#     values = (name, job_title, department, location, phone, emergency_contact, employee_id)
#     mycursor.execute(sql, values)
#     mydb.commit()

#     return 'Employee updated successfully'

# # 删除员工路由
# @app.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
# def delete_employee(employee_id):
#     sql = "DELETE FROM employees WHERE employee_id = %s"
#     values = (employee_id,)
#     mycursor.execute(sql, values)
#     mydb.commit()
#     return 'Employee deleted successfully'

# # 出勤状况路由
# @app.route('/attendance')
# def attendance():
#     return render_template('attendance.html')

# # 员工资料路由
# @app.route('/employee_data')
# def employee_data():
#     mycursor.execute("SELECT * FROM employees")
#     employees = mycursor.fetchall()
#     return render_template('employee_data.html', employees=employees)

# # 个人资料页面路由
# @app.route('/employee/<int:employee_id>')
# def employee_profile(employee_id):
#     mycursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
#     employee = mycursor.fetchone()
#     if employee:
#         personal_files = employee[7].split(',')
#         return render_template('employee_profile.html', employee=employee, personal_files=personal_files)
#     else:
#         return 'Employee not found'

# if __name__ == '__main__':
#     app.run(debug=True)
