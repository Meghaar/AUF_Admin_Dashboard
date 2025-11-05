# db_init.py
import sqlite3
from werkzeug.security import generate_password_hash
from flask import g
import os

DB = os.getenv("DB_PATH", "auf_admin.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db(app):
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