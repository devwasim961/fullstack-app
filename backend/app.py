
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import time

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host':     os.environ.get('DB_HOST',     'db'),
    'user':     os.environ.get('DB_USER',     'appuser'),
    'password': os.environ.get('DB_PASSWORD', 'apppass'),
    'database': os.environ.get('DB_NAME',     'appdb')
}

def get_db():
    retries = 5
    while retries:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            print(f"DB connection failed: {e}. Retrying...")
            retries -= 1
            time.sleep(3)
    raise Exception("Cannot connect to database")

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id    INT AUTO_INCREMENT PRIMARY KEY,
            name  VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized ✅")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "Backend is running ✅"})

@app.route('/users', methods=['GET'])
def get_users():
    try:
        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users")
        users  = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def add_user():
    try:
        data  = request.get_json()
        name  = data.get('name')
        email = data.get('email')
        if not name or not email:
            return jsonify({"error": "Name and email required"}), 400
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            (name, email)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "User added successfully"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── init_db removed from here ──
# DB initialises on first request now
# not on startup

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
