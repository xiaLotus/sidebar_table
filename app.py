from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS 

app = Flask(__name__)
CORS(app, supports_credentials=True)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 初始化資料庫
with get_db_connection() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL
                  )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sidebar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_name TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                  )''')
    conn.commit()

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if not user:
        conn.execute('INSERT INTO users (username) VALUES (?)', (username,))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    conn.close()
    return jsonify({'message': 'Login successful', 'user_id': user['id'], 'username': user['username']})

@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({'message': 'Logged out successfully'})

@app.route('/sidebar', methods=['GET', 'POST', 'DELETE'])
def sidebar():
    user_id = request.headers.get('User-ID')  # 🔥 前端要在 headers 傳 `user_id`
    
    if not user_id:
        return jsonify({'error': 'Unauthorized - No User ID'}), 401

    conn = get_db_connection()
    
    if request.method == 'GET':
        items = conn.execute('SELECT * FROM sidebar WHERE user_id = ?', (user_id,)).fetchall()
        return jsonify([dict(item) for item in items])

    elif request.method == 'POST':
        item_name = request.json.get('item_name')
        conn.execute('INSERT INTO sidebar (user_id, item_name) VALUES (?, ?)', (user_id, item_name))
        conn.commit()
        return jsonify({'message': 'Sidebar item added'})

    elif request.method == 'DELETE':
        item_id = request.json.get('id')
        conn.execute('DELETE FROM sidebar WHERE id = ? AND user_id = ?', (item_id, user_id))
        conn.commit()
        return jsonify({'message': 'Sidebar item deleted'})

    conn.close()

@app.route('/view-db', methods=['GET'])
def view_db():
    conn = get_db_connection()
    
    # 取得 users 資料
    users = conn.execute("SELECT * FROM users").fetchall()
    users_list = [dict(user) for user in users]
    
    # 取得 sidebar 資料
    sidebar = conn.execute("SELECT * FROM sidebar").fetchall()
    sidebar_list = [dict(item) for item in sidebar]

    conn.close()

    return jsonify({
        "users": users_list,
        "sidebar": sidebar_list
    })


if __name__ == '__main__':
    app.run(debug=True)
