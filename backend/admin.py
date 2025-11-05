# admin.py
from flask import request, jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from auth import admin_required
from db_init import get_db
import datetime

# ---------- Admin Endpoints ----------

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