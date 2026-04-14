# Momentum App — Setup & Run

## ⚠️ Important: Do NOT open index.html directly
The app **must** be run through Flask. Opening `index.html` directly in your browser will cause "Failed to fetch" errors because the browser can't reach the API.

## Quick Start

```bash
# 1. Put all files in the same folder:
#    app.py, database.py, and a /static folder containing index.html

# 2. Install Flask if needed:
pip install flask

# 3. Run the server:
python app.py

# 4. Open your browser and go to:
#    http://localhost:5000
```

> ✅ Always use `http://localhost:5000` — never open `index.html` directly.

## First-time setup
The database (`momentum.db`) is created automatically on first run.

To seed a demo admin account, run:
```bash
python database.py
```
This creates:
- `student@college.edu` / `password123`
- `admin@momentum.app` / `adminpass1` (admin)

## Project Structure
```
momentum/
├── app.py          # Flask API routes
├── database.py     # SQLite schema + all DB operations
├── momentum.db     # Auto-created on first run
└── static/
    └── index.html  # Full frontend (served by Flask)
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/register | Create account |
| POST | /api/login | Log in |
| POST | /api/logout | Log out |
| GET  | /api/me | Current session user |
| GET  | /api/tasks | List user's tasks |
| POST | /api/tasks | Create task |
| POST | /api/tasks/:id/toggle | Toggle complete |
| POST | /api/tasks/:id/postpone | Increment postponement |
| DELETE | /api/tasks/:id | Delete task |
| GET  | /api/admin/stats | Admin: system stats |
| GET  | /api/admin/users | Admin: all users |
| DELETE | /api/admin/users/:id | Admin: delete user |

## Security Notes
- Passwords hashed with PBKDF2-HMAC-SHA256 (260,000 iterations, OWASP 2024)
- Each password has a unique 256-bit random salt
- Constant-time comparison prevents timing attacks
- Sessions expire on browser close
- Foreign keys enforced (cascade deletes tasks when user is deleted)
- Change `SECRET_KEY` env var before deploying to production
