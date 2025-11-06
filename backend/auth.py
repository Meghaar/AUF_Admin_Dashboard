# auth.py
import datetime
import jwt
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
from db_init import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretdevkey")  # change in production
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = 60 * 60 * 8  # 8 hours

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

# ---------- Authentication Endpoints ----------

def login():
    data = request.json or {}
    username = data.get("username")
    is_admin = data.get("is_admin")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    db = get_db()
    
    # Select must_reset column to check if password change is required
    cur = db.execute(
        "SELECT slno, username, password, is_admin, must_reset FROM users WHERE username = ?", 
        (username,)
    )
    row = cur.fetchone()
    
    if is_admin:
        if row["is_admin"] == 0:
            return jsonify({"error": "Admin authorization"}), 401

    if not row:
        return jsonify({"error": "invalid credentials"}), 401

    if not check_password_hash(row["password"], password):
        return jsonify({"error": "invalid credentials"}), 401

    # Check if user must reset password (admin reset scenario)
    must_reset_password = row["must_reset"] if row["must_reset"] is not None else False
    
    # Update last login time
    db.execute(
        "UPDATE users SET last_login_time = ? WHERE slno = ?",
        (datetime.datetime.now(), row["slno"])
    )
    db.commit()

    user = {
        "slno": row["slno"], 
        "username": row["username"], 
        "is_admin": row["is_admin"],
        "must_reset": must_reset_password  # Add this flag
    }
    token = create_token(user)
    return jsonify({
        "access_token": token, 
        "user": user,
        "must_reset": must_reset_password  # Also include in response
    })

def me():
    return jsonify({"user": request.user})

def change_password():
    data = request.json or {}
    old = data.get("old_password")
    new = data.get("new_password")
    username = data.get("username")
    
    if not old or not new:
        return jsonify({"error": "old_password and new_password required"}), 400

    db = get_db()
    cur = db.execute("SELECT password, must_reset FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    
    if not row:
        return jsonify({"error": "user not found"}), 404

    if not check_password_hash(row["password"], old):
        return jsonify({"error": "old password incorrect"}), 401

    # Update password and clear the must_reset flag
    db.execute(
        "UPDATE users SET password = ?, reset_password_time = ?, must_reset = FALSE WHERE username = ?",
        (generate_password_hash(new), datetime.datetime.now(), username)
    )
    db.commit()
    return jsonify({"message": "password updated", "success": True})

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

def change_own_password():
    # This endpoint uses the authenticated user from token
    data = request.json or {}
    old = data.get("old_password")
    new = data.get("new_password")
    
    if not old or not new:
        return jsonify({"success": False, "message": "old_password and new_password required"}), 400

    user_id = request.user["user_id"]
    username = request.user["username"]
    
    db = get_db()
    cur = db.execute("SELECT password, must_reset FROM users WHERE slno = ?", (user_id,))
    row = cur.fetchone()
    
    if not row:
        return jsonify({"success": False, "message": "user not found"}), 404

    if not check_password_hash(row["password"], old):
        return jsonify({"success": False, "message": "old password incorrect"}), 401

    # Update password and clear the must_reset flag
    db.execute(
        "UPDATE users SET password = ?, reset_password_time = ?, must_reset = FALSE WHERE slno = ?",
        (generate_password_hash(new), datetime.datetime.now(), user_id)
    )
    db.commit()
    
    return jsonify({
        "success": True,
        "message": "password updated successfully"
    })

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