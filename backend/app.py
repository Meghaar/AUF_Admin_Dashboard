# app.py
from flask import Flask, render_template
from flask_cors import CORS  # Add this import
from dotenv import load_dotenv
import os
from db_init import init_db, close_db
from auth import login, me, change_password, change_username, forgot_request, auth_required,change_own_password
from admin import admin_change_credentials, admin_create_user, admin_forgot_requests, admin_reset_user_password, list_users

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretdevkey")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Enable CORS for all routes - Add this line
CORS(app, origins=["http://localhost:4200"], supports_credentials=True)

# Register teardown
app.teardown_appcontext(close_db)

# ---------- Authentication Routes ----------
app.add_url_rule("/api/login", view_func=login, methods=["POST"])
app.add_url_rule("/api/me", view_func=me, methods=["GET"])
app.add_url_rule("/api/change_password", view_func=change_password, methods=["POST","PUT"])
app.add_url_rule("/api/change_username", view_func=change_username, methods=["POST"])
app.add_url_rule("/api/forgot_request", view_func=forgot_request, methods=["POST"])
app.add_url_rule("/api/change_own_password", view_func=change_own_password, methods=["PUT"])

# ---------- Admin Routes ----------
app.add_url_rule("/api/admin/change_credentials", view_func=admin_change_credentials, methods=["POST","PUT"])
app.add_url_rule("/api/admin/create_user", view_func=admin_create_user, methods=["POST"])
app.add_url_rule("/api/admin/forgot_requests", view_func=admin_forgot_requests, methods=["GET"])
app.add_url_rule("/api/admin/reset_user_password", view_func=admin_reset_user_password, methods=["POST"])
app.add_url_rule("/api/users", view_func=list_users, methods=["GET"])

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
    init_db(app)
    DB = os.getenv("DB_PATH", "auf_admin.db")
    print(f"Database initialized at: {DB}")
    print("Default admin credentials: admin / admin123")
    app.run(debug=True)