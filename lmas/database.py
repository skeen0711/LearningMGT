# database.py (update or create)
import sqlite3

def init_db():
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    # Existing tables (users, courses, assignments)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, is_admin INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses 
                 (id INTEGER PRIMARY KEY, name TEXT, filepath TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS assignments 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER, due_date TEXT, 
                  FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(course_id) REFERENCES courses(id))''')
    # New attempts table
    c.execute('''CREATE TABLE IF NOT EXISTS attempts 
                 (attempt_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  course_id TEXT, 
                  correct_responses INTEGER, 
                  incorrect_responses INTEGER, 
                  passed INTEGER, 
                  start_time TEXT, 
                  end_time TEXT, 
                  score REAL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def add_user(username, password, is_admin):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)",
              (username, password, is_admin))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def add_course(name, filepath):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT INTO courses (name, filepath) VALUES (?, ?)", (name, filepath))
    conn.commit()
    conn.close()

def get_all_courses():
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT * FROM courses")
    courses = c.fetchall()
    conn.close()
    return courses

def assign_course(user_id, course_id, due_date):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT INTO assignments (user_id, course_id, due_date) VALUES (?, ?, ?)",
              (user_id, course_id, due_date))
    conn.commit()
    conn.close()

def get_assignments(user_id):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute('''SELECT c.name, c.filepath, a.due_date, p.score, p.passed 
                 FROM assignments a 
                 JOIN courses c ON a.course_id = c.id 
                 LEFT JOIN attempts p ON a.user_id = p.user_id AND c.filepath = p.course_id 
                 WHERE a.user_id = ? 
                 ORDER BY p.end_time DESC LIMIT 1''', (user_id,))
    assignments = c.fetchall()
    conn.close()
    return assignments

def get_all_users():
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()
    return users

def save_attempt(user_id, course_id, correct_responses, incorrect_responses, passed, start_time, end_time, score):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute('''INSERT INTO attempts (user_id, course_id, correct_responses, incorrect_responses, passed, start_time, end_time, score) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, course_id, correct_responses, incorrect_responses, passed, start_time, end_time, score))
    conn.commit()
    conn.close()

def get_attempts(user_id):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT * FROM attempts WHERE user_id = ?", (user_id,))
    attempts = c.fetchall()
    conn.close()
    return attempts