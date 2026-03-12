"""
app.py — Flask REST API for Momentum productivity app
"""

from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
import os
import re

from database import (
    init_db,
    create_user, authenticate_user, get_user_by_id,
    get_all_users, delete_user,
    create_task, get_tasks_for_user, toggle_task_complete,
    update_postponements, delete_task, tick_overdue_postponements,
    get_admin_stats,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod-32chars!!")

# Serve files from the same directory as app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Global error handler — always returns JSON, never HTML 500 ────────────────

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    traceback.print_exc()
    return jsonify({"error": "Server error", "detail": str(e)}), 500


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not authenticated"}), 401
        user = get_user_by_id(session["user_id"])
        if not user or not user["is_admin"]:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


def current_user():
    return get_user_by_id(session["user_id"])


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    # force=True accepts body even without Content-Type header
    # silent=True returns None instead of raising on bad JSON
    data = request.get_json(force=True, silent=True) or {}
    email    = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not re.match(r"[^@]+@[^@]+", email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    user = create_user(email, password)
    if user is None:
        return jsonify({"error": "Email already registered"}), 409

    return jsonify({"message": "Account created. Please log in."}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    email    = (data.get("email") or "").strip()
    password = data.get("password") or ""

    user = authenticate_user(email, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    # Tick overdue postponements on login
    tick_overdue_postponements(user["id"])

    session.clear()
    session["user_id"] = user["id"]
    session.permanent = False  # expires on browser close

    return jsonify({
        "user": {
            "id":       user["id"],
            "email":    user["email"],
            "is_admin": bool(user["is_admin"]),
        }
    }), 200


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.route("/api/me", methods=["GET"])
@login_required
def me():
    user = current_user()
    return jsonify({
        "id":       user["id"],
        "email":    user["email"],
        "is_admin": bool(user["is_admin"]),
    })


# ── Task routes ───────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
@login_required
def list_tasks():
    tasks = get_tasks_for_user(session["user_id"])
    return jsonify(tasks)


@app.route("/api/tasks", methods=["POST"])
@login_required
def add_task():
    data = request.get_json(force=True, silent=True) or {}
    title    = (data.get("title") or "").strip()
    due_date = data.get("due_date") or ""
    parent   = data.get("parent_task_id")

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 100:
        return jsonify({"error": "Title max 100 characters"}), 400
    if not re.match(r"\d{4}-\d{2}-\d{2}", due_date):
        return jsonify({"error": "due_date must be YYYY-MM-DD"}), 400

    task = create_task(session["user_id"], title, due_date, parent)
    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = toggle_task_complete(task_id, session["user_id"])
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@app.route("/api/tasks/<int:task_id>/postpone", methods=["POST"])
@login_required
def postpone_task(task_id):
    task = update_postponements(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def remove_task(task_id):
    ok = delete_task(task_id, session["user_id"])
    if not ok:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Deleted"}), 200


# ── Admin routes ──────────────────────────────────────────────────────────────

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def admin_stats():
    return jsonify(get_admin_stats())


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def admin_users():
    return jsonify(get_all_users())


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def admin_delete_user(user_id):
    if user_id == session["user_id"]:
        return jsonify({"error": "Cannot delete yourself"}), 400
    ok = delete_user(user_id)
    if not ok:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted"}), 200


# ── Serve frontend ────────────────────────────────────────────────────────────

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    # Try static/ subfolder first, then fall back to same directory as app.py
    for base in [os.path.join(BASE_DIR, "static"), BASE_DIR]:
        if path:
            full = os.path.join(base, path)
            if os.path.isfile(full):
                return send_from_directory(base, path)
        index = os.path.join(base, "index.html")
        if os.path.isfile(index):
            return send_from_directory(base, "index.html")
    return "index.html not found. Make sure index.html is in the same folder as app.py", 404


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)