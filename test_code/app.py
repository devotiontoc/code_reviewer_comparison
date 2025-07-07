# app.py
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'users.db'

def get_db_connection():
    """Establishes a connection to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        conn.execute(
            'CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)'
        )
        conn.execute("INSERT INTO users (name, email) VALUES (?, ?)",
                     ('Admin User', 'admin@example.com'))
        conn.commit()
        conn.close()

@app.route('/users', methods=['GET'])
def get_users():
    """Fetches all users from the database."""
    conn = get_db_connection()
    users = conn.execute('SELECT id, name, email FROM users').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in users])

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Fetches a single user by their ID."""
    conn = get_db_connection()
    user = conn.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)