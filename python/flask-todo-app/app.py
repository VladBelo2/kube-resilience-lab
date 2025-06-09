from flask import Flask, render_template, request, redirect, url_for
from prometheus_client import Counter, generate_latest
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "todo.db"

# Metrics
TASKS_ADDED = Counter('todo_tasks_added_total', 'Total tasks added')
TASKS_COMPLETED = Counter('todo_tasks_completed_total', 'Total tasks completed')
TASKS_DELETED = Counter('todo_tasks_deleted_total', 'Total tasks deleted')

# DB Init
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    completed BOOLEAN NOT NULL DEFAULT 0)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, content, completed FROM tasks')
    tasks = c.fetchall()
    conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    content = request.form.get('content')
    if content:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO tasks (content, completed) VALUES (?, 0)', (content,))
        conn.commit()
        conn.close()
        TASKS_ADDED.inc()
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    TASKS_COMPLETED.inc()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    TASKS_DELETED.inc()
    return redirect(url_for('index'))

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
