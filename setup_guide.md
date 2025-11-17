# 🚀 Attendance Management System - Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git (optional)
- Google Cloud account for OAuth

---

## 📥 Step 1: Installation

### 1.1 Clone or Download the Project

```bash
cd attendance-system
```

### 1.2 Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Step 2: Google OAuth Setup

### 2.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google+ API**

### 2.2 Create OAuth Credentials

1. Navigate to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Configure consent screen:
   - User Type: **Internal** (for organization) or **External**
   - App name: **Attendance System**
   - Add your domain
4. Application type: **Web application**
5. Add Authorized redirect URI:
   ```
   http://localhost:5000/auth/callback
   ```
   For production, use your actual domain:
   ```
   https://yourdomain.com/auth/callback
   ```

6. Copy **Client ID** and **Client Secret**

---

## ⚙️ Step 3: Configuration

### 3.1 Create .env File

```bash
cp .env.example .env
```

### 3.2 Edit .env File

Open `.env` and fill in your details:

```bash
# Generate a secure secret key
FLASK_SECRET_KEY=your-very-secure-random-secret-key

# Google OAuth from Step 2
GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here

# Domain restriction (only these emails can log in)
ALLOWED_DOMAIN=iitj.ac.in

# Super Admin emails (comma-separated)
ADMINS=admin@iitj.ac.in,teacher@iitj.ac.in
```

**🔐 Security Tips:**
- Generate a strong secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
- Never commit `.env` to version control
- Change secret key in production

---

## 🗄️ Step 4: Database Setup

The app uses SQLite by default. PostgreSQL is also supported.

### 4.1 SQLite (Default - No Setup Required)

Database file `app.db` will be created automatically on first run.

### 4.2 PostgreSQL (Optional)

If you want to use PostgreSQL:

1. Install PostgreSQL
2. Create a database:
   ```sql
   CREATE DATABASE attendance_db;
   ```
3. Update `.env`:
   ```bash
   DATABASE_URL=postgresql://username:password@localhost/attendance_db
   ```

---

## ▶️ Step 5: Run the Application

### 5.1 Start the Server

```bash
python run.py
```

Or using Flask CLI:

```bash
export FLASK_APP=run.py  # On Windows: set FLASK_APP=run.py
flask run
```

### 5.2 Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

---

## 👥 Step 6: Create Users

### 6.1 First Login

1. Click **Sign in** on the homepage
2. Log in with your `@iitj.ac.in` Google account
3. First user will be created as **Student** by default

### 6.2 Promote to Admin

#### Option A: Via .env (Recommended for first admin)

Add your email to `ADMINS` in `.env`:
```bash
ADMINS=youremail@iitj.ac.in
```

Restart the server.

#### Option B: Via Database (If you already have an admin)

```bash
# Open Python shell
python

# Run this:
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email='youremail@iitj.ac.in').first()
    user.role = 'admin'
    db.session.commit()
    print(f'{user.email} is now admin')
```

### 6.3 Promote to Teacher

1. Log in as admin
2. Go to Admin Dashboard → Manage Users
3. Click **Promote** next to the user

---

## 🧪 Step 7: Testing the System

### 7.1 As Admin

1. Navigate to `/admin`
2. View all users, promote/demote roles
3. Monitor system activity

### 7.2 As Teacher

1. Login with teacher account
2. Create a room: **Rooms** → **New Room**
3. Start a session: **Start Session**
4. Share PIN or QR code with students

### 7.3 As Student

1. Login with student account
2. Wait for active session
3. Mark attendance using PIN or QR

---

## 🔧 Troubleshooting

### Issue: "OAuth initialization failed"

**Solution:** Check if `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correctly set in `.env`

### Issue: "Only institutional emails are allowed"

**Solution:** Make sure your email ends with the domain specified in `ALLOWED_DOMAIN` (default: `iitj.ac.in`)

### Issue: "404 Not Found" on routes

**Solution:** Make sure all blueprints are registered in `app/__init__.py`

### Issue: Database errors

**Solution:** Delete `app.db` and restart the server to recreate tables

### Issue: Can't access admin panel

**Solution:** 
1. Check if your email is in `ADMINS` in `.env`
2. Restart the server after editing `.env`
3. Or promote via database (see Step 6.2)

---

## 📊 Features Overview

### ✅ For Students
- Mark attendance via PIN or QR code
- View attendance history
- Real-time session status
- Device fingerprint verification

### ✅ For Teachers
- Create and manage rooms (courses)
- Start/stop attendance sessions
- Live attendance monitoring
- Export attendance to CSV
- QR code generation

### ✅ For Admins
- User management (promote/demote/ban)
- System-wide monitoring
- View all rooms and sessions
- Access all attendance records

---

## 🚀 Production Deployment

### Security Checklist

- [ ] Set strong `FLASK_SECRET_KEY`
- [ ] Use HTTPS (not HTTP)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set `FLASK_ENV=production`
- [ ] Enable secure cookies: `SESSION_COOKIE_SECURE=True`
- [ ] Use a proper WSGI server (Gunicorn/uWSGI)
- [ ] Set up firewall rules
- [ ] Regular database backups

### Sample Production Config

```bash
# .env (production)
FLASK_SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:pass@db-host/attendance_prod
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
ALLOWED_DOMAIN=iitj.ac.in
ADMINS=admin@iitj.ac.in
FLASK_ENV=production
```

### Deploy with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review error logs in console
3. Check Flask documentation
4. Verify Google OAuth setup

---

## 📝 Quick Reference

| Route | Access | Description |
|-------|--------|-------------|
| `/` | Public | Landing page |
| `/auth/login` | Public | Login |
| `/dashboard` | Student | Student dashboard |
| `/teacher/dashboard` | Teacher | Teacher dashboard |
| `/admin` | Admin | Admin dashboard |

---

**🎉 You're all set! Enjoy using the Attendance Management System!**