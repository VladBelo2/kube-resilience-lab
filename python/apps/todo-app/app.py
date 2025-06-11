from flask import Flask, render_template, request, redirect, url_for
from prometheus_client import Counter, Gauge, generate_latest
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "todo.db"

# Prometheus metrics
TASKS_TOTAL = Gauge('todo_tasks_total', 'Total number of tasks')
TASKS_ACTIVE = Gauge('todo_tasks_active', 'Active (incomplete) tasks')
TASKS_COMPLETED = Gauge('todo_tasks_completed', 'Completed tasks')
TASKS_DELETED = Counter('todo_tasks_deleted_total', 'Total tasks deleted')

# DB Init
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def update_metrics():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM tasks')
    TASKS_TOTAL.set(c.fetchone()[0])
    c.execute('SELECT COUNT(*) FROM tasks WHERE completed = 0')
    TASKS_ACTIVE.set(c.fetchone()[0])
    c.execute('SELECT COUNT(*) FROM tasks WHERE completed = 1')
    TASKS_COMPLETED.set(c.fetchone()[0])
    conn.close()

@app.route('/')
def index():
    filter_by = request.args.get('filter', 'all')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if filter_by == 'active':
        c.execute('SELECT * FROM tasks WHERE completed = 0')
    elif filter_by == 'completed':
        c.execute('SELECT * FROM tasks WHERE completed = 1')
    else:
        c.execute('SELECT * FROM tasks')

    tasks = c.fetchall()
    conn.close()

    update_metrics()
    return render_template('index.html', tasks=tasks, current_filter=filter_by)

@app.route('/add', methods=['POST'])
def add():
    content = request.form.get('content')
    if content:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO tasks (content, completed) VALUES (?, 0)', (content,))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/complete/<int:id>')
def complete(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE tasks SET completed = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
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
