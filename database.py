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
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # WAL mode prevents lock conflicts
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            is_admin      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id            INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title              TEXT    NOT NULL CHECK(length(title) <= 100),
            due_date           TEXT    NOT NULL,
            completed          INTEGER NOT NULL DEFAULT 0,
            completed_at       TEXT,
            postponement_count INTEGER NOT NULL DEFAULT 0,
            parent_task_id     INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
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
    _migrate()


def _migrate():
    conn = get_db()
    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()]
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
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260000,
    )
    return dk.hex()


def hash_password(password):
    salt = secrets.token_hex(32)
    return _hash_password(password, salt), salt


def verify_password(password, stored_hash, salt):
    return secrets.compare_digest(_hash_password(password, salt), stored_hash)


# ── User helpers ──────────────────────────────────────────────────────────────

def create_user(email, password, is_admin=False):
    pw_hash, salt = hash_password(password)
    try:
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, salt, is_admin) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), pw_hash, salt, int(is_admin)),
        )
        conn.commit()
        uid = cur.lastrowid
        conn.close()
        return get_user_by_id(uid)
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
    if priority not in ("high", "medium", "low"):
        priority = "medium"
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO tasks (user_id, title, due_date, parent_task_id, priority) VALUES (?, ?, ?, ?, ?)",
        (user_id, title.strip(), due_date, parent_task_id, priority),
    )
    conn.commit()
    tid = cur.lastrowid
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
    if not task or task["user_id"] != user_id:
        return None
    now_complete = not bool(task["completed"])
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
    conn = get_db()
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM users)                     AS total_users,
            (SELECT COUNT(*) FROM tasks)                     AS total_tasks,
            (SELECT COUNT(*) FROM tasks WHERE completed = 1) AS completed_tasks
    """).fetchone()
    conn.close()
    return dict(row)
