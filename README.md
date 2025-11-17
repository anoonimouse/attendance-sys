# Attendance App (Flask)

**What this is:** A minimal, ready-to-run Flask webapp for marking student attendance using Google OAuth restricted to `@iitj.ac.in` emails.

**Features included:**
- Google OAuth login (Authlib)
- Domain restriction to `@iitj.ac.in`
- Roles: student, teacher, admin (promote/demote via DB)
- Create rooms, open timed attendance slots, mark attendance
- Export attendance CSV
- SQLite database (file: `app.db`)
- Tailwind-like modern UI via CDN (Tailwind Play CDN)

**Requirements**
- Python 3.10+
- Install dependencies: `pip install -r requirements.txt`

**Setup**
1. Copy `.env.example` to `.env` and fill in the Google OAuth credentials.
   - Create OAuth credentials in Google Cloud Console (OAuth 2.0 Client IDs)
   - Authorized redirect URI: `http://localhost:5000/auth/callback`
2. `export FLASK_APP=run.py` (or set in Windows)
3. `flask run` or `python run.py`

**Notes**
- You must set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.
- For production, use HTTPS and secure cookie settings.

Enjoy — edit code under `app/` to customize!
