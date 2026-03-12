def update_postponements(task_id: int) -> dict | None:
    """Increment postponement_count by 1."""
    conn = get_db()
    conn.execute(
        "UPDATE tasks SET postponement_count = postponement_count + 1 WHERE id = ?",
        (task_id,),
    )
    conn.commit()
    conn.close()
    return get_task_by_id(task_id)


def delete_task(task_id: int, user_id: int) -> bool:
    conn = get_db()
    cur = conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def tick_overdue_postponements(user_id: int) -> int:
    """
    Called on login: increment postponement_count for every task that is
    overdue (due_date < today), not completed, and not already counted today.
    Returns number of tasks updated.
    Simple approach: increment for all qualifying tasks each login session
    (for MVP; in prod you'd track last-checked date).
    """
    conn = get_db()
    cur = conn.execute(
        """UPDATE tasks
           SET postponement_count = postponement_count + 1
           WHERE user_id = ?
             AND completed = 0
             AND due_date < date('now')""",
        (user_id,),
    )
    conn.commit()
    count = cur.rowcount
    conn.close()
    return count


# ── Admin stats ───────────────────────────────────────────────────────────────

def get_admin_stats() -> dict:
    conn = get_db()
    stats = conn.execute("""
                         SELECT
                                 (SELECT COUNT(*) FROM users)                     AS total_users,
                                 (SELECT COUNT(*) FROM tasks)                     AS total_tasks,
                                 (SELECT COUNT(*) FROM tasks WHERE completed = 1) AS completed_tasks
                         """).fetchone()
    conn.close()
    return dict(stats)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    # Seed a demo user and an admin for testing
    print("\n── Seeding demo data ──")

    u = create_user("student@college.edu", "password123")
    print(f"Created user:  {u}")

    admin = create_user("admin@momentum.app", "adminpass1", is_admin=True)
    print(f"Created admin: {admin}")

    # Verify login works
    auth = authenticate_user("student@college.edu", "password123")
    print(f"\nLogin OK: {auth['email']}")

    bad = authenticate_user("student@college.edu", "wrongpass")
    print(f"Bad login:  {bad}")

    # Create some tasks
    t1 = create_task(u["id"], "Submit biology lab report", "2025-06-01")
    t2 = create_task(u["id"], "Read chapters 4-6", "2025-06-15")
    print(f"\nTasks: {get_tasks_for_user(u['id'])}")

    # Admin stats
    print(f"\nAdmin stats: {get_admin_stats()}")
