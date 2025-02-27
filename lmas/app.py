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
    manifest_path = os.path.join(extract_path, 'imsmanifest.xml')
    if not os.path.exists(manifest_path):
        return 'index.html'
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    for resource in root.findall('.//{http://www.imsglobal.org/xsd/imscp_v1p1}resource'):
        if resource.get('type') == 'webcontent':
            href = resource.get('href', 'index.html')
            return href
    return 'index.html'


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


@app.route('/content/<path:filepath>/<filename>')
def serve_content(filepath, filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if filename.endswith('.html'):
        with open(os.path.join(CONTENT_DIR, filepath, filename), 'r') as f:
            content = f.read()
        script_tag = '''
            <script src="/static/scorm_api.js"></script>
            <script>
                console.log("Injecting SCORM overrides");
                pipwerks.SCORM.version = "1.2";  // Force SCORM 1.2
                pipwerks.debug.isActive = true;  // Enable debug
                pipwerks.SCORM.API.handle = window.API;  // Force API handle
                pipwerks.SCORM.API.isFound = true;  // Mark as found
                console.log("API handle set:", pipwerks.SCORM.API.handle);
                console.log("Forcing SCORM init");
                pipwerks.SCORM.init();
                var originalCalcScore2 = window.calcScore2 || function() {};
                window.calcScore2 = function() {
                    console.log("calcScore2 called, computing score");
                    originalCalcScore2();
                    var score = window.actualScore;
                    console.log("Setting score:", score);
                    pipwerks.SCORM.set("cmi.core.score.raw", score);
                    pipwerks.SCORM.set("cmi.core.lesson_status", score >= 90 ? "completed" : "incomplete");
                    setTimeout(function() {
                        console.log("Triggering LMSFinish after score set");
                        pipwerks.SCORM.quit();
                    }, 1000);  // Increased delay for stability
                };
            </script>
        '''
        if '<body' in content:
            body_start = content.index('<body') + content[content.index('<body'):].index('>') + 1
            content = content[:body_start] + script_tag + content[body_start:]
        else:
            content = script_tag + content
        print(f"Serving {filename} with scorm_api.js and overrides injected")
        return content, 200, {'Content-Type': 'text/html'}
    return send_from_directory(os.path.join(CONTENT_DIR, filepath), filename)


@app.route('/scorm_api', methods=['POST'])
def scorm_api():
    if 'user_id' not in session or 'current_course' not in session:
        print("SCORM API: Unauthorized access attempt")
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    print(f"SCORM API call: {data}")
    command = data.get('command')
    key = data.get('key')
    value = data.get('value')

    # Ensure scorm_data exists and has interactions sub-dictionary
    if 'scorm_data' not in session or not isinstance(session['scorm_data'], dict):
        session['scorm_data'] = {'interactions': {}}
    if 'interactions' not in session['scorm_data']:
        session['scorm_data']['interactions'] = {}

    if command == 'LMSInitialize':
        session['scorm_data'] = {'start_time': datetime.now().isoformat(), 'interactions': {}}
        return jsonify({"success": True})
    elif command == 'LMSSetValue':
        if key.startswith('cmi.interactions'):
            session['scorm_data']['interactions'][key] = value
        else:
            session['scorm_data'][key] = value
        session.modified = True
        return jsonify({"success": True})
    elif command == 'LMSFinish':
        scorm_data = session.get('scorm_data', {})
        course_filepath = session['current_course']
        # Use filepath directly instead of course tuple
        assignments = database.get_assignments(session['user_id'])
        course = next((a for a in assignments if a[1] == course_filepath), None)  # a[1] is filepath
        if course:
            score = float(scorm_data.get('cmi.core.score.raw', 0))
            status = scorm_data.get('cmi.core.lesson_status', 'incomplete')
            passed = 1 if status in ['completed', 'passed'] and score >= 80 else 0

            # Count all interaction results explicitly
            interactions = scorm_data.get('interactions', {})
            correct_responses = 0
            incorrect_responses = 0
            for i in range(10):  # 10 questions
                result_key = f'cmi.interactions.{i}.result'
                resp_key = f'cmi.interactions.{i}.student_response'
                corr_key = f'cmi.interactions.{i}.correct_responses.0.pattern'
                if result_key in interactions:
                    if interactions[result_key] == 'correct':
                        correct_responses += 1
                    elif interactions[result_key] == 'wrong':
                        incorrect_responses += 1
                # Fallback: Compare student_response to correct_response if result is missing
                elif resp_key in interactions and corr_key in interactions:
                    if interactions[resp_key] == interactions[corr_key]:
                        correct_responses += 1
                    else:
                        incorrect_responses += 1

            print(
                f"Saving attempt: user={session['user_id']}, course={course_filepath}, score={score}, status={status}, correct={correct_responses}, incorrect={incorrect_responses}")
            database.save_attempt(
                session['user_id'],
                course_filepath,
                correct_responses,
                incorrect_responses,
                passed,
                scorm_data.get('start_time', datetime.now().isoformat()),
                datetime.now().isoformat(),
                score
            )
        else:
            print(f"Attempt not saved: course not found for filepath={course_filepath}, assignments={assignments}")
        session.pop('current_course', None)
        session.pop('scorm_data', None)
        return jsonify({"success": True})
    return jsonify({"error": "Invalid command"}), 400

@app.route('/nevow_liveOutput', methods=['GET', 'POST'])
def nevow_live_output():
    print("Nevow liveOutput called")
    return jsonify({"status": "ok"}), 200


@app.route('/nevow_liveInput', methods=['GET', 'POST'])
def nevow_live_input():
    print("Nevow liveInput called")
    return jsonify({"status": "ok"}), 200


@app.route('/authoring', methods=['GET', 'POST'])
def authoring():
    print("Authoring called")
    return jsonify({"status": "ok"}), 200


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        print("POST request received at /admin_dashboard")
        if 'add_user' in request.form:
            username = request.form['username']
            password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            database.add_user(username, password.decode('utf-8'), is_admin=0)
            print(f"User added: {username}")
        elif 'add_course' in request.form:
            name = request.form.get('course_name', '')
            print(f"Course name: {name}")
            if 'course_file' in request.files:
                file = request.files['course_file']
                print(f"File received: {file.filename}")
                if file and file.filename:
                    if file.filename.lower().endswith('.zip'):
                        filepath = os.path.join(COURSE_DIR, file.filename)
                        file.save(filepath)
                        database.add_course(name, file.filename)
                        print(f"Course saved: {filepath}")
                    else:
                        print(f"Invalid file type: {file.filename}, must be .zip")
                else:
                    print("No file uploaded or empty filename")
            else:
                print("No course_file in request.files")
        elif 'assign_course' in request.form:
            user_id = request.form['user_id']
            course_id = request.form['course_id']
            due_date = request.form['due_date']
            database.assign_course(user_id, course_id, due_date)
            print(f"Course assigned: user_id={user_id}, course_id={course_id}, due_date={due_date}")

    users = database.get_all_users()
    courses = database.get_all_courses()
    assignments = database.get_assignments(session['user_id'])
    # Fetch attempts with user info
    all_attempts = []
    user_dict = {user[0]: user[1] for user in users}  # Map user_id to username
    for user in users:
        user_attempts = database.get_attempts(user[0])
        for attempt in user_attempts:
            all_attempts.append((user_dict[user[0]],) + attempt)  # Prepend username
    return render_template('admin_dashboard.html', users=users, courses=courses, assignments=assignments, attempts=all_attempts)

if __name__ == '__main__':
    if not os.path.exists(COURSE_DIR):
        os.makedirs(COURSE_DIR)
    if not os.path.exists(CONTENT_DIR):
        os.makedirs(CONTENT_DIR)
    hashed_pw = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    if not database.get_user('admin'):
        database.add_user('admin', hashed_pw, is_admin=1)
    app.run(debug=True)