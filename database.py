"""
database.py — SQLite setup for Momentum app
Tables: users, tasks
"""

import sqlite3
import hashlib
import secrets
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "momentum.db")


def get_db():
    """Return a database connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT  NOT NULL,
            salt        TEXT    NOT NULL,
            is_admin    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title             TEXT    NOT NULL CHECK(length(title) <= 100),
            due_date          TEXT    NOT NULL,
            completed         INTEGER NOT NULL DEFAULT 0,
            completed_at      TEXT,
            postponement_count INTEGER NOT NULL DEFAULT 0,
            parent_task_id    INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_tasks_user_id   ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date  ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Database initialised at {DB_PATH}")


# ── Password helpers ──────────────────────────────────────────────────────────

def _hash_password(password: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256, 260 000 iterations (OWASP 2024 recommendation)."""
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260_000,
    )
    return dk.hex()


def hash_password(password: str) -> tuple[str, str]:
    """Return (password_hash, salt) for a new password."""
    salt = secrets.token_hex(32)          # 256-bit random salt
    return _hash_password(password, salt), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    candidate = _hash_password(password, salt)
    return secrets.compare_digest(candidate, stored_hash)


# ── User operations ───────────────────────────────────────────────────────────

def create_user(email: str, password: str, is_admin: bool = False) -> dict | None:
    """
    Insert a new user. Returns the user row dict or None if email already exists.
    """
    pw_hash, salt = hash_password(password)
    try:
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO users (email, password_hash, salt, is_admin) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), pw_hash, salt, int(is_admin)),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None          # duplicate email


def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> dict | None:
    """Return user dict on success, None on failure."""
    user = get_user_by_email(email)
    if not user:
        return None
    if verify_password(password, user["password_hash"], user["salt"]):
        return user
    return None


def get_all_users() -> list[dict]:
    """Admin: list all users (no password data)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, email, is_admin, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id: int) -> bool:
    """Admin: delete user + cascade-delete their tasks."""
    conn = get_db()
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# ── Task operations ───────────────────────────────────────────────────────────

def create_task(user_id: int, title: str, due_date: str,
                parent_task_id: int | None = None) -> dict:
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO tasks (user_id, title, due_date, parent_task_id)
           VALUES (?, ?, ?, ?)""",
        (user_id, title.strip(), due_date, parent_task_id),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return get_task_by_id(task_id)


def get_task_by_id(task_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tasks_for_user(user_id: int) -> list[dict]:
    """Return all tasks for a user sorted by due_date asc."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date ASC, id ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_task_complete(task_id: int, user_id: int) -> dict | None:
    """Toggle completed status. Resets postponement_count on completion."""
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
