"""
app.py — Flask REST API for Momentum productivity app
"""

from flask import Flask, request, jsonify, session, send_from_directory
from functools import wraps
import os
import re

# Load .env file (no external packages needed)
_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env):
    for _line in open(_env):
        _line = _line.strip()
        # Ignore comments and malformed lines
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            # Only set env variable if not already defined to prevent overrides
            os.environ.setdefault(_k.strip(), _v.strip())

from database import (
    init_db,
    create_user, authenticate_user, get_user_by_id,
    get_all_users, get_all_users_with_metrics, delete_user,
    create_task, get_tasks_for_user, toggle_task_complete,
    update_postponements, update_task_priority, delete_task,
    tick_overdue_postponements, get_admin_stats,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod-32chars!!")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    traceback.print_exc() # Logs full stack trace to console for debugging
    msg = str(e) if str(e) else "Server error"
    return jsonify({"error": msg}), 500 # Always return JSON instead of crashing


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Ensures users is logged in before accessing proctected routes
        if "user_id" not in session:
            return jsonify({"error": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Check authorization
        if "user_id" not in session:
            return jsonify({"error": "Not authenticated"}), 401

        # 2. Check admin privileges
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
    try:
        # Updates postponement penalties for overdue tasks at login time
        tick_overdue_postponements(user["id"])
    except Exception as ex:
        print("tick_overdue_postponements failed:", ex)
    session.clear() # Prevent session fixation attacks
    session["user_id"] = user["id"]
    session.permanent = False # Session expires after browser closes
    return jsonify({"user": {"id": user["id"], "email": user["email"], "is_admin": bool(user["is_admin"])}}), 200

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@app.route("/api/me", methods=["GET"])
@login_required
def me():
    user = current_user()
    return jsonify({"id": user["id"], "email": user["email"], "is_admin": bool(user["is_admin"])})


# ── Task routes ───────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
@login_required
def list_tasks():
    return jsonify(get_tasks_for_user(session["user_id"]))

@app.route("/api/tasks", methods=["POST"])
@login_required
def add_task():
    data     = request.get_json(force=True, silent=True) or {}
    title    = (data.get("title") or "").strip()
    due_date = data.get("due_date") or ""
    parent   = data.get("parent_task_id")
    priority = data.get("priority", "medium")

    # Validation checks to maintain clean DB data
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if len(title) > 100:
        return jsonify({"error": "Title max 100 characters"}), 400

    # Ensures strict YYYY-MM-DD format to avoid parsing issues
    if not re.match(r"\d{4}-\d{2}-\d{2}", due_date):
        return jsonify({"error": "due_date must be YYYY-MM-DD"}), 400

    # Create task in DB
    task = create_task(session["user_id"], title, due_date, parent, priority)
    return jsonify(task), 201

@app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    # Flips completed status (true <-> false)
    task = toggle_task_complete(task_id, session["user_id"])
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route("/api/tasks/<int:task_id>/priority", methods=["PATCH"])
@login_required
def set_priority(task_id):
    data     = request.get_json(force=True, silent=True) or {}
    priority = data.get("priority", "medium")
    task = update_task_priority(task_id, session["user_id"], priority)
    if not task:
        return jsonify({"error": "Task not found or invalid priority"}), 404
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


@app.route("/api/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    return jsonify({
        "stats": get_admin_stats(),
        "users": get_all_users_with_metrics(),
    })


# ── Serve frontend ────────────────────────────────────────────────────────────

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    for base in [os.path.join(BASE_DIR, "static"), BASE_DIR]:
        if path:
            full = os.path.join(base, path)
            if os.path.isfile(full):
                return send_from_directory(base, path)
        index = os.path.join(base, "index.html")
        if os.path.isfile(index):
            return send_from_directory(base, "index.html")
    return "index.html not found. Make sure index.html is in the same folder as app.py", 404


if __name__ == "__main__":
    init_db()
    # ── Auto-create hardcoded admin account on every startup ──────────────────
    from database import create_user, get_user_by_email
    import sqlite3 as _sq3
    _ADMIN_EMAIL    = "yiqiao.huang@ufl.edu"
    _ADMIN_PASSWORD = "adminpass1"          # change this to whatever you want
    # Create if doesn't exist
    if not get_user_by_email(_ADMIN_EMAIL):
        create_user(_ADMIN_EMAIL, _ADMIN_PASSWORD, is_admin=True)
        print(f"[Admin] Created admin account: {_ADMIN_EMAIL}")
    else:
        # Make sure is_admin=1 even if account already exists
        _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'momentum.db')
        conn = _sq3.connect(_db_path)
        conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (_ADMIN_EMAIL,))
        conn.commit()
        conn.close()
        print(f"[Admin] Admin account confirmed: {_ADMIN_EMAIL}")
    # ──────────────────────────────────────────────────────────────────────────

    # Debug mode ON for development, should be OFF in production
    app.run(debug=True, port=5000, use_reloader=False, threaded=False)

# ── AI Feedback route ─────────────────────────────────────────────────────────

@app.route("/api/ai-feedback", methods=["POST"])
@login_required
def ai_feedback():
    import urllib.request, urllib.error, json as _json, datetime

    api_key = os.environ.get("OPENAI_API_KEY", "")

    # Prevent API call if key is missing
    if not api_key or api_key == "YOUR_NEW_KEY_HERE":
        return jsonify({"error": "OpenAI API key not configured. Add it to your .env file."}), 503

    data     = request.get_json(force=True, silent=True) or {}
    mode     = data.get("mode", "full")   # full | schedule | gpa | burnout | weekly
    context  = data.get("context", {})    # task data sent from frontend

    today_str = datetime.date.today().isoformat()

    # Build a rich task summary for the prompt
    tasks_raw = context.get("tasks", [])
    total     = len(tasks_raw)

    # Compute useful analytics for prompt engineering
    completed = sum(1 for t in tasks_raw if t.get("completed"))
    overdue   = [t for t in tasks_raw if not t.get("completed") and t.get("due_date","") < today_str]
    upcoming  = [t for t in tasks_raw if not t.get("completed") and t.get("due_date","") >= today_str]
    
    # Detect behavioral patterns, important for the AI insight
    postponed = [t for t in tasks_raw if t.get("postponement_count", 0) >= 3]
    high_pri  = [t for t in tasks_raw if t.get("priority") == "high" and not t.get("completed")]

    def fmt_task(t):
        # Formats tasks into readable bullet points for LLM prompt
        p = t.get("postponement_count", 0)
        return f"- [{t.get('priority','medium').upper()}] \"{t.get('title','')}\" due {t.get('due_date','')}{'  ⚠️ postponed '+str(p)+'x' if p >= 3 else ''}"

    task_lines = "\n".join(fmt_task(t) for t in tasks_raw) or "No tasks yet."

    mode_instructions = {
        "full": """Provide ALL of the following sections clearly labeled:
1. TASK OVERLOAD WARNING — is the student overloaded? What's at risk?
2. GPA MAXIMIZER PLAN — a concrete day-by-day or week-by-week study plan ordering tasks by academic impact
3. BURNOUT RISK SCORE — score 1-10 with explanation and specific advice
4. WEEKLY PRIORITIES RECAP — the top 3-5 things they must focus on this week in priority order
5. PERSONALIZED TIPS — 2-3 specific, actionable suggestions based on their exact task list""",

        "schedule": """Create a detailed OPTIMAL STUDY SCHEDULE for the next 7 days.
For each day list specific tasks to work on and approximate time blocks.
Order by due date urgency and priority level. Be concrete and specific.""",

        "gpa": """Create a GPA MAXIMIZER PLAN.
Identify which tasks have the highest academic impact and should be prioritized.
Suggest a study sequence that maximizes performance on high-stakes work.
Include time estimates and any tasks that should be broken down further.""",

        "burnout": """Perform a detailed BURNOUT RISK ASSESSMENT.
Score burnout risk 1-10. Explain the key stress factors from their task list.
Give 3-5 specific, personalized strategies to reduce burnout risk.
Flag any immediate concerns.""",

        "weekly": """Create a WEEKLY PRIORITIES RECAP.
List the top 5 tasks for this week in order of importance.
Explain why each is prioritized. Flag anything overdue that needs immediate attention.""",
    }

    system_prompt = """You are an expert academic coach and productivity advisor for college students.
You analyze student task lists and provide highly personalized, actionable advice.
Be specific, encouraging, and direct. Use the actual task names in your advice.
Format your response with clear section headers using emoji. Keep it focused and practical."""

    user_prompt = f"""Today is {today_str}.

STUDENT'S TASK DATA:
- Total tasks: {total}
- Completed: {completed}
- Overdue: {len(overdue)}
- Upcoming: {len(upcoming)}
- High priority incomplete: {len(high_pri)}
- Repeatedly postponed (3+ times): {len(postponed)}

FULL TASK LIST:
{task_lines}

{mode_instructions.get(mode, mode_instructions['full'])}

Be specific — reference actual task names from the list above."""

    payload = _json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": 1200, # Prevent overly long responses
        "temperature": 0.7, # Balanced creativity vs determinism
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            text = result["choices"][0]["message"]["content"]
            return jsonify({"feedback": text})

    # Handles API-specific errors
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return jsonify({"error": f"OpenAI error: {body}"}), 502

    # Handles general failures
    except Exception as e:
        return jsonify({"error": str(e)}), 502
