import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        filepath TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        due_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        score REAL,
        passed INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )''')
    conn.commit()
    conn.close()

def add_user(username, password, is_admin=0):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
              (username, password, is_admin))
    conn.commit()
    conn.close()

def add_course(name, filepath):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT INTO courses (name, filepath) VALUES (?, ?)", (name, filepath))
    conn.commit()
    conn.close()

def assign_course(user_id, course_id, due_date):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT INTO assignments (user_id, course_id, due_date) VALUES (?, ?, ?)",
              (user_id, course_id, due_date))
    conn.commit()
    conn.close()

def save_progress(user_id, course_id, start_time, end_time, score, passed):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("INSERT INTO progress (user_id, course_id, start_time, end_time, score, passed) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, course_id, start_time, end_time, score, passed))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_assignments(user_id):
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT courses.name, courses.filepath, assignments.due_date, progress.score, progress.passed \
               FROM assignments \
               LEFT JOIN courses ON assignments.course_id = courses.id \
               LEFT JOIN progress ON assignments.user_id = progress.user_id AND assignments.course_id = progress.course_id \
               WHERE assignments.user_id = ?", (user_id,))
    assignments = c.fetchall()
    conn.close()
    return assignments

def get_all_users():
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE is_admin = 0")
    users = c.fetchall()
    conn.close()
    return users

def get_all_courses():
    conn = sqlite3.connect('lmas.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM courses")
    courses = c.fetchall()
    conn.close()
    return courses

if __name__ == "__main__":
    init_db()