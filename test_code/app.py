from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'users.db'
# Flaw 1: Hardcoded Secret Key (Security)
app.config['SECRET_KEY'] = 'my-super-secret-key-that-is-very-bad-to-have-in-code'

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
    # Flaw 2: Inefficient Data Handling (Performance)
    # This fetches all users then manually constructs a list, which is less efficient
    # for large datasets than direct serialization.
    conn = get_db_connection()
    users_cursor = conn.execute('SELECT id, name, email FROM users').fetchall()
    conn.close()

    user_list = []
    for user in users_cursor:
        user_list.append({'id': user['id'], 'name': user['name'], 'email': user['email']})
    return jsonify(user_list)

@app.route('/user/search', methods=['GET'])
def search_user():
    """Searches for a user by name."""
    name = request.args.get('name')
    conn = get_db_connection()

    # Flaw 3: SQL Injection Vulnerability (Security)
    query = f"SELECT id, name, email FROM users WHERE name = '{name}'"
    user = conn.execute(query).fetchone()

    conn.close()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Fetches a single user by their ID."""
    conn = get_db_connection()
    user = conn.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,)).fetchone()
    # Flaw 4: Unclosed DB Connection in one path (Bug/Resource Leak)
    if user is None:
        # The connection is not closed here.
        return jsonify({'error': 'User not found'}), 404

    # Flaw 5: Useless variable (Code Smell/Style)
    is_user_found = True

    conn.close()
    return jsonify(dict(user))

# Flaw 6: Unused function (Code Smell/Style)
def a_function_that_is_not_used():
    magic_number = 42 # Flaw 7: Magic Number
    return magic_number * 2

if __name__ == '__main__':
    init_db()
    # Flaw 8: Running in Debug Mode in a production-like script (Security)
    app.run(debug=True)