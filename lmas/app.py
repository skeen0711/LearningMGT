from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import bcrypt
import zipfile
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import database

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure key
COURSE_DIR = os.path.join(os.getcwd(), 'courses')
CONTENT_DIR = os.path.join(os.getcwd(), 'content')

# Initialize database
database.init_db()


def get_scorm_entry_point(extract_path):
    """Parse imsmanifest.xml to find the entry point HTML file."""
    manifest_path = os.path.join(extract_path, 'imsmanifest.xml')
    if not os.path.exists(manifest_path):
        return 'index.html'  # Fallback
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    # SCORM 1.2: Look for the first resource with type 'webcontent'
    for resource in root.findall('.//{http://www.imsglobal.org/xsd/imscp_v1p1}resource'):
        if resource.get('type') == 'webcontent':
            href = resource.get('href', 'index.html')
            return href
    return 'index.html'  # Default if not found


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


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))


@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    assignments = database.get_assignments(session['user_id'])
    return render_template('user_dashboard.html', assignments=assignments)


@app.route('/launch_course/<path:filepath>')
def launch_course(filepath):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    zip_path = os.path.join(COURSE_DIR, filepath)
    extract_path = os.path.join(CONTENT_DIR, filepath.replace('.zip', ''))

    if not os.path.exists(extract_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

    entry_point = get_scorm_entry_point(extract_path)
    if os.path.exists(os.path.join(extract_path, entry_point)):
        session['current_course'] = filepath
        return redirect(url_for('serve_content', filepath=filepath.replace('.zip', ''), filename=entry_point))
    return "Course entry point not found", 404


## RevStart -- Inject SCORM API script into HTML to ensure API availability
@app.route('/content/<path:filepath>/<filename>')
def serve_content(filepath, filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if filename.endswith('.html'):
        with open(os.path.join(CONTENT_DIR, filepath, filename), 'r') as f:
            content = f.read()
        script_tag = '<script src="/static/scorm_api.js"></script>'
        if '<head>' in content:
            content = content.replace('<head>', f'<head>{script_tag}')
        else:
            content = script_tag + content
        return content, 200, {'Content-Type': 'text/html'}
    return send_from_directory(os.path.join(CONTENT_DIR, filepath), filename)


## RevEnd

## RevStart -- Enhanced SCORM API with debug logging
@app.route('/scorm_api', methods=['POST'])
def scorm_api():
    if 'user_id' not in session or 'current_course' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    print(f"SCORM API call: {data}")  # Debug logging to verify calls
    command = data.get('command')
    key = data.get('key')
    value = data.get('value')

    if command == 'LMSInitialize':
        session['scorm_data'] = {'start_time': datetime.now().isoformat()}
        return jsonify({"success": True})
    elif command == 'LMSSetValue':
        session['scorm_data'][key] = value
        return jsonify({"success": True})
    elif command == 'LMSFinish':
        scorm_data = session.get('scorm_data', {})
        course_filepath = session['current_course']
        course = next((a for a in database.get_assignments(session['user_id']) if a[1] == course_filepath), None)
        if course and 'cmi.core.score.raw' in scorm_data:
            database.save_progress(
                session['user_id'],
                course_filepath,
                scorm_data.get('start_time', datetime.now().isoformat()),
                datetime.now().isoformat(),
                float(scorm_data.get('cmi.core.score.raw', 0)),
                1 if scorm_data.get('cmi.core.lesson_status', 'incomplete') in ['completed', 'passed'] else 0
            )
        session.pop('current_course', None)
        session.pop('scorm_data', None)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid command"}), 400


## RevEnd

## RevStart -- Stub out Nevow endpoints to silence errors
@app.route('/nevow_liveOutput', methods=['GET', 'POST'])
def nevow_live_output():
    print("Nevow liveOutput called")  # Debug logging
    return jsonify({"status": "ok"}), 200


@app.route('/nevow_liveInput', methods=['GET', 'POST'])
def nevow_live_input():
    print("Nevow liveInput called")  # Debug logging
    return jsonify({"status": "ok"}), 200


@app.route('/authoring', methods=['GET', 'POST'])
def authoring():
    print("Authoring called")  # Debug logging
    return jsonify({"status": "ok"}), 200


## RevEnd

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
            if file and file.filename.endswith('.zip'):
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
    assignments = database.get_assignments(session['user_id'])
    return render_template('admin_dashboard.html', users=users, courses=courses, assignments=assignments)


if __name__ == '__main__':
    if not os.path.exists(COURSE_DIR):
        os.makedirs(COURSE_DIR)
    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)
    hashed_pw = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    if not database.get_user('admin'):
        database.add_user('admin', hashed_pw, is_admin=1)
    app.run(debug=True)