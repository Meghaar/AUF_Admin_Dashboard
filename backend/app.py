# app.py
import sqlite3
import datetime
from functools import wraps
from flask import Flask, request, jsonify, g, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from dotenv import load_dotenv
import os

load_dotenv()

DB = os.getenv("DB_PATH", "auf_admin.db")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretdevkey")  # change in production
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = 60 * 60 * 8  # 8 hours

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with a single table"""
    with app.app_context():
        db = get_db()
        
        # Create single users table with all details
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                slno INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE NOT NULL,
                must_reset BOOLEAN DEFAULT FALSE,
                reset_requested BOOLEAN DEFAULT FALSE,
                last_login_time DATETIME,
                reset_password_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                forgot_request_status TEXT DEFAULT NULL,
                forgot_request_time DATETIME DEFAULT NULL,
                admin_note TEXT DEFAULT NULL
            )
        """)
        
        # Check if admin user exists, if not create one
        cur = db.execute("SELECT slno FROM users WHERE is_admin = 1")
        admin_exists = cur.fetchone()
        
        if not admin_exists:
            # Create default admin user
            default_admin_username = "admin"
            default_admin_password = "admin123"  # Change this in production!
            hashed_password = generate_password_hash(default_admin_password)
            
            db.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                (default_admin_username, hashed_password, True)
            )
            print("Default admin user created:")
            print(f"Username: {default_admin_username}")
            print(f"Password: {default_admin_password}")
            print("Please change these credentials after first login!")
        
        db.commit()

def create_token(user):
    payload = {
        "user_id": user["slno"],
        "username": user["username"],
        "is_admin": user["is_admin"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_SECONDS)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        # attach user info to request context
        request.user = payload
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        if not payload.get("is_admin"):
            return jsonify({"error": "Admin privileges required"}), 403
        request.user = payload
        return fn(*args, **kwargs)
    return wrapper


# ---------- API Endpoints ----------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    cur = db.execute("SELECT slno, username, password, is_admin FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "invalid credentials"}), 401

    if not check_password_hash(row["password"], password):
        return jsonify({"error": "invalid credentials"}), 401

    # Update last login time
    db.execute(
        "UPDATE users SET last_login_time = ? WHERE slno = ?",
        (datetime.datetime.now(), row["slno"])
    )
    db.commit()

    user = {"slno": row["slno"], "username": row["username"], "is_admin": row["is_admin"]}
    token = create_token(user)
    return jsonify({"access_token": token, "user": user})

@app.route("/api/me", methods=["GET"])
@auth_required
def me():
    return jsonify({"user": request.user})

@app.route("/api/change_password", methods=["POST"])
@auth_required
def change_password():
    data = request.json or {}
    old = data.get("old_password")
    new = data.get("new_password")
    if not old or not new:
        return jsonify({"error": "old_password and new_password required"}), 400

    user_id = request.user["user_id"]
    db = get_db()
    cur = db.execute("SELECT password FROM users WHERE slno = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "user not found"}), 404

    if not check_password_hash(row["password"], old):
        return jsonify({"error": "old password incorrect"}), 401

    db.execute(
        "UPDATE users SET password = ?, reset_password_time = ? WHERE slno = ?",
        (generate_password_hash(new), datetime.datetime.now(), user_id)
    )
    db.commit()
    return jsonify({"message": "password updated"})

@app.route("/api/change_username", methods=["POST"])
@auth_required
def change_username():
    # Only allow admin to change username
    if not request.user.get("is_admin"):
        return jsonify({"error": "Only admin can change username"}), 403
        
    data = request.json or {}
    new_username = data.get("new_username")
    password = data.get("password")  # Require password confirmation for security
    
    if not new_username or not password:
        return jsonify({"error": "new_username and password required"}), 400

    user_id = request.user["user_id"]
    db = get_db()
    
    # Verify current password
    cur = db.execute("SELECT password, is_admin FROM users WHERE slno = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "user not found"}), 404

    if not check_password_hash(row["password"], password):
        return jsonify({"error": "password incorrect"}), 401

    # If user is admin, check if another admin exists (only one admin allowed)
    if row["is_admin"]:
        cur = db.execute("SELECT slno FROM users WHERE is_admin = 1 AND slno != ?", (user_id,))
        other_admins = cur.fetchall()
        if other_admins:
            return jsonify({"error": "Cannot change admin username when other admins exist"}), 400

    # Check if new username is already taken
    cur = db.execute("SELECT slno FROM users WHERE username = ? AND slno != ?", (new_username, user_id))
    if cur.fetchone():
        return jsonify({"error": "username already taken"}), 400

    # Update username
    db.execute("UPDATE users SET username = ? WHERE slno = ?", (new_username, user_id))
    db.commit()
    
    return jsonify({"message": "username updated successfully"})

@app.route("/api/admin/change_credentials", methods=["POST"])
@admin_required
def admin_change_credentials():
    """Allows admin to change both username and password in one request"""
    data = request.json or {}
    current_password = data.get("current_password")
    new_username = data.get("new_username")
    new_password = data.get("new_password")
    
    if not current_password:
        return jsonify({"error": "current_password is required"}), 400
    
    if not new_username and not new_password:
        return jsonify({"error": "Either new_username or new_password is required"}), 400

    user_id = request.user["user_id"]
    db = get_db()
    
    # Verify current password and get user info
    cur = db.execute("SELECT password, username, is_admin FROM users WHERE slno = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"error": "user not found"}), 404

    if not check_password_hash(row["password"], current_password):
        return jsonify({"error": "current password is incorrect"}), 401

    # If changing username
    if new_username and new_username != row["username"]:
        # Check if new username is available
        cur = db.execute("SELECT slno FROM users WHERE username = ? AND slno != ?", (new_username, user_id))
        if cur.fetchone():
            return jsonify({"error": "username already taken"}), 400
        
        # For admin, ensure we maintain only one admin
        if row["is_admin"]:
            cur = db.execute("SELECT slno FROM users WHERE is_admin = 1 AND slno != ?", (user_id,))
            other_admins = cur.fetchall()
            if other_admins:
                return jsonify({"error": "Cannot change admin credentials when other admins exist"}), 400
        
        db.execute("UPDATE users SET username = ? WHERE slno = ?", (new_username, user_id))

    # If changing password
    if new_password:
        db.execute(
            "UPDATE users SET password = ?, reset_password_time = ? WHERE slno = ?",
            (generate_password_hash(new_password), datetime.datetime.now(), user_id)
        )

    db.commit()
    
    return jsonify({"message": "credentials updated successfully"})

@app.route("/api/admin/create_user", methods=["POST"])
@admin_required
def admin_create_user():
    """Admin creates a new user"""
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    
    # Check if username already exists
    cur = db.execute("SELECT slno FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        return jsonify({"error": "username already exists"}), 400

    # Create new user (non-admin by default)
    hashed_password = generate_password_hash(password)
    db.execute(
        "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
        (username, hashed_password, False)
    )
    db.commit()
    
    return jsonify({"message": "user created successfully"}), 201

@app.route("/api/forgot_request", methods=["POST"])
def forgot_request():
    data = request.json or {}
    username = data.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400

    db = get_db()
    cur = db.execute("SELECT slno FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        # to avoid leaking info, we can return success even if user not found
        return jsonify({"message": "If the username exists, a request has been recorded."}), 200

    user_id = row["slno"]
    # Update the user record with forgot request
    db.execute(
        "UPDATE users SET forgot_request_status = 'pending', forgot_request_time = ? WHERE slno = ?",
        (datetime.datetime.now(), user_id)
    )
    db.commit()
    return jsonify({"message": "forgot password request created"}), 201

@app.route("/api/admin/forgot_requests", methods=["GET"])
@admin_required
def admin_forgot_requests():
    db = get_db()
    cur = db.execute("""
        SELECT slno as user_id, username, forgot_request_time as requested_at, 
               forgot_request_status as status, admin_note
        FROM users 
        WHERE forgot_request_status = 'pending'
        ORDER BY forgot_request_time DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"requests": rows})

@app.route("/api/admin/reset_user_password", methods=["POST"])
@admin_required
def admin_reset_user_password():
    data = request.json or {}
    user_id = data.get("user_id")
    new_password = data.get("new_password")
    note = data.get("admin_note", "")

    if not user_id or not new_password:
        return jsonify({"error": "user_id and new_password required"}), 400

    db = get_db()
    cur = db.execute("SELECT slno FROM users WHERE slno = ?", (user_id,))
    if not cur.fetchone():
        return jsonify({"error": "user not found"}), 404

    db.execute(
        "UPDATE users SET password = ?, forgot_request_status = 'resolved', admin_note = ? WHERE slno = ?",
        (generate_password_hash(new_password), note, user_id)
    )
    db.commit()
    return jsonify({"message": "user password reset by admin"})

@app.route("/api/users", methods=["GET"])
@admin_required
def list_users():
    db = get_db()
    cur = db.execute("""
        SELECT slno, username, is_admin, must_reset, reset_requested, 
               last_login_time, reset_password_time, created_at,
               forgot_request_status, forgot_request_time, admin_note
        FROM users 
        ORDER BY slno
    """)
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"users": rows})

# ---------- Basic test UI routes (Very basic) ----------
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/user")
def user_dashboard():
    return render_template("user.html")

@app.route("/admin")
def admin_dashboard():
    return render_template("admin.html")

# ---------- Run app ----------
if __name__ == "__main__":
    # Initialize database
    init_db()
    print(f"Database initialized at: {DB}")
    print("Default admin credentials: admin / admin123")
    app.run(debug=True)