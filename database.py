"""
database.py — SQLite setup for Momentum app
Uses check_same_thread=False and short-lived connections to avoid threading issues.
"""

import sqlite3
import hashlib
import secrets
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "momentum.db")


def get_db():
    # Create a new DB connection per call to avoid threading issues in Flask
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    # Allows accessing columns like dicts instead of tuples
    conn.row_factory = sqlite3.Row

    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE COLLATE NOCASE, -- case-insensitive uniqueness
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            is_admin      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title              TEXT    NOT NULL CHECK(length(title) <= 100), -- enforce max length
            due_date           TEXT    NOT NULL,
            completed          INTEGER NOT NULL DEFAULT 0,
            completed_at       TEXT,
            postponement_count INTEGER NOT NULL DEFAULT 0,
            parent_task_id     INTEGER REFERENCES tasks(id) ON DELETE CASCADE, -- supports subtasks
            priority           TEXT    NOT NULL DEFAULT 'medium',
            created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_user_id   ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date  ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);
    """)
    conn.commit()
    conn.close()
    print("[DB] Ready: " + DB_PATH)

    # Run migrations after ensuring base schema exists
    _migrate()


def _migrate():
    # Handles schema updates without dropping the DB 
    conn = get_db()
    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]

        # If priority column doesn't exist, add it
        if "priority" not in cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
            conn.commit()
            print("[DB] Migrated: added priority column")
    except Exception as e:
        print("[DB] Migration warning: " + str(e))
    finally:
        conn.close()


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(password, salt):
    # PBDKDF2 = slow hashing to protect agaisnt brute force attacks
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260000, # high iteration count = stronger security
    )
    return dk.hex()


def hash_password(password):
    # Generate a secure random salt to prevent rainbow table attacks
    salt = secrets.token_hex(32)
    return _hash_password(password, salt), salt


def verify_password(password, stored_hash, salt):
    # Constant-time comparison prevents timing attacks
    return secrets.compare_digest(_hash_password(password, salt), stored_hash)


# ── User helpers ──────────────────────────────────────────────────────────────

def create_user(email, password, is_admin=False):
    pw_hash, salt = hash_password(password)
    try:
        conn = get_db()
        cur = conn.execute(
            # Normalize email (lowercase + trim) to avoid duplicates
            "INSERT INTO users (email, password_hash, salt, is_admin) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), pw_hash, salt, int(is_admin)),
        )
        conn.commit()
        uid = cur.lastrowid # Get auto-generated user ID
        conn.close()
        return get_user_by_id(uid)

    # IF email already exists
    except sqlite3.IntegrityError:
        return None


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and verify_password(password, user["password_hash"], user["salt"]):
        return user
    return None


def get_all_users():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, email, is_admin, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id):
    conn = get_db()
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# ── Task helpers ──────────────────────────────────────────────────────────────

def create_task(user_id, title, due_date, parent_task_id=None, priority="medium"):
    # Enforce allowed priority values
    if priority not in ("high", "medium", "low"):
        priority = "medium"
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO tasks (user_id, title, due_date, parent_task_id, priority) VALUES (?, ?, ?, ?, ?)",
        (user_id, title.strip(), due_date, parent_task_id, priority),
    )
    conn.commit()
    tid = cur.lastrowid # Get new task ID
    conn.close()
    return get_task_by_id(tid)


def get_task_by_id(task_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tasks_for_user(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date ASC, id ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_task_complete(task_id, user_id):
    task = get_task_by_id(task_id)

    # Ensure user owns the task (basic authorization check)
    if not task or task["user_id"] != user_id:
        return None
    now_complete = not bool(task["completed"]) # flip status
    conn = get_db()
    conn.execute(
        """UPDATE tasks
           SET completed = ?,
               completed_at = CASE WHEN ? THEN datetime('now') ELSE NULL END,
               postponement_count = CASE WHEN ? THEN 0 ELSE postponement_count END
           WHERE id = ?""",
        (int(now_complete), now_complete, now_complete, task_id),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def update_postponements(task_id):
    conn = get_db()

    # Increment postponement count (used for burnout/AI insights)
    conn.execute(
        "UPDATE tasks SET postponement_count = postponement_count + 1 WHERE id = ?",
        (task_id,),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def update_task_priority(task_id, user_id, priority):
    if priority not in ("high", "medium", "low"):
        return None
    conn = get_db()
    cur = conn.execute(
        "UPDATE tasks SET priority = ? WHERE id = ? AND user_id = ?",
        (priority, task_id, user_id),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id) if cur.rowcount > 0 else None


def delete_task(task_id, user_id):
    conn = get_db()
    cur = conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def tick_overdue_postponements(user_id):
    try:
        conn = get_db()

        # Automatically penalize overdue incomplete tasks
        cur = conn.execute(
            """UPDATE tasks SET postponement_count = postponement_count + 1
               WHERE user_id = ? AND completed = 0 AND due_date < date('now')""",
            (user_id,),
        )
        conn.commit()
        n = cur.rowcount
        conn.close()
        return n
    except Exception as e:
        print("[DB] tick error: " + str(e))
        return 0


def get_admin_stats():
    """System-wide stats for the admin dashboard."""
    conn = get_db()
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM users)                                            AS total_users,
            (SELECT COUNT(*) FROM tasks)                                            AS total_tasks,
            (SELECT COUNT(*) FROM tasks WHERE completed = 1)                        AS completed_tasks,
            (SELECT COUNT(*) FROM tasks WHERE completed = 0)                        AS pending_tasks,
            (SELECT COUNT(*) FROM tasks WHERE completed = 0
                AND due_date < date('now'))                                         AS overdue_tasks,
            (SELECT COUNT(*) FROM tasks WHERE postponement_count >= 3
                AND completed = 0)                                                  AS at_risk_tasks,
            (SELECT COUNT(*) FROM tasks WHERE priority = 'high')                    AS high_priority_tasks,
            (SELECT ROUND(AVG(task_count), 1) FROM (
                SELECT COUNT(*) AS task_count FROM tasks GROUP BY user_id))         AS avg_tasks_per_user,
            (SELECT ROUND(AVG(done_count * 100.0 / NULLIF(total_count, 0)), 1)
             FROM (SELECT
                     COUNT(*) AS total_count,
                     SUM(completed) AS done_count
                   FROM tasks GROUP BY user_id))                                    AS avg_completion_rate
    """).fetchone()
    conn.close()
    return dict(row)


def get_all_users_with_metrics():
    """Admin: each user with their own task metrics."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            u.id,
            u.email,
            u.is_admin,
            u.created_at,
            COUNT(t.id)                                             AS total_tasks,
            COALESCE(SUM(t.completed), 0)                          AS completed_tasks,
            COALESCE(SUM(CASE WHEN t.completed = 0 THEN 1 END), 0) AS pending_tasks,
            COALESCE(SUM(CASE WHEN t.completed = 0
                AND t.due_date < date('now') THEN 1 END), 0)       AS overdue_tasks,
            COALESCE(SUM(CASE WHEN t.postponement_count >= 3
                AND t.completed = 0 THEN 1 END), 0)                AS at_risk_tasks,
            COALESCE(SUM(CASE WHEN t.priority = 'high'
                AND t.completed = 0 THEN 1 END), 0)                AS high_priority_pending,
            CASE WHEN COUNT(t.id) > 0
                THEN ROUND(SUM(t.completed) * 100.0 / COUNT(t.id), 0)
                ELSE 0 END                                          AS completion_rate,
            MAX(t.completed_at)                                     AS last_active
        FROM users u
        LEFT JOIN tasks t ON t.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
