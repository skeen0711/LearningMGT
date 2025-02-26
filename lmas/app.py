from flask import Flask, render_template, request, redirect, url_for, session
import bcrypt
import subprocess
from datetime import datetime
import os
import database

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure key
COURSE_DIR = os.path.join(os.getcwd(), 'courses')

# Initialize database
database.init_db()


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        user = database.get_user(username)
        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['is_admin'] = user[3]
            if user[3]:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        return "Invalid credentials"
    return render_template('login.html')


@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    assignments = database.get_assignments(session['user_id'])
    return render_template('user_dashboard.html', assignments=assignments)


@app.route('/launch_course/</Applications/eXeLearning.app>')
def launch_course(filepath):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    start_time = datetime.now().isoformat()
    subprocess.Popen(['exelearning', os.path.join(COURSE_DIR, filepath)])  # Adjust path/command as needed
    # Placeholder: In practice, you'd need a way to get end_time, score, and passed from eXelearning
    # For now, simulate completion manually or extend later
    return redirect(url_for('user_dashboard'))


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'add_user' in request.form:
            username = request.form['username']
            password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            database.add_user(username, password.decode('utf-8'), is_admin=0)
        elif 'add_course' in request.form:
            name = request.form['course_name']
            file = request.files['course_file']
            if file and file.filename.endswith('.elp'):
                filepath = os.path.join(COURSE_DIR, file.filename)
                file.save(filepath)
                database.add_course(name, file.filename)
        elif 'assign_course' in request.form:
            user_id = request.form['user_id']
            course_id = request.form['course_id']
            due_date = request.form['due_date']
            database.assign_course(user_id, course_id, due_date)

    users = database.get_all_users()
    courses = database.get_all_courses()
    assignments = database.get_assignments(session['user_id'])  # For display, adjust as needed
    return render_template('admin_dashboard.html', users=users, courses=courses, assignments=assignments)


if __name__ == '__main__':
    if not os.path.exists(COURSE_DIR):
        os.makedirs(COURSE_DIR)
    # Create an admin user (for initial setup)
    hashed_pw = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    if not database.get_user('admin'):
        database.add_user('admin', hashed_pw, is_admin=1)
    app.run(debug=True)