# app/auth.py

from flask import Blueprint, redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user
from authlib.integrations.flask_client import OAuth
from .models import User
from . import db
import requests

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

oauth = OAuth()

def init_oauth(app):
    """Called by create_app() inside __init__.py"""
    oauth.init_app(app)

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# -----------------------
# LOGIN ROUTE
# -----------------------

@auth_bp.route("/login")
def login():
    try:
        redirect_uri = url_for("auth.callback", _external=True)
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        flash(f"OAuth initialization failed: {e}", "danger")
        return redirect("/")


# -----------------------
# GOOGLE CALLBACK
# -----------------------

@auth_bp.route("/callback")
def callback():
    """Handles the Google OAuth callback"""
    try:
        # 1️⃣ Step: Exchange code for token
        token = oauth.google.authorize_access_token()
        client = oauth.google

        # 2️⃣ Fetch Google OpenID metadata
        metadata = client.load_server_metadata()

        # 3️⃣ Secure userinfo endpoint
        userinfo_url = metadata.get("userinfo_endpoint")

        if not userinfo_url:
            flash("Google login failed: userinfo endpoint missing.", "danger")
            return redirect(url_for("auth.login"))

        # 4️⃣ Request user info
        resp = requests.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {token['access_token']}"}
        )

        if resp.status_code != 200:
            flash("Failed to fetch Google profile info.", "danger")
            return redirect(url_for("auth.login"))

        userinfo = resp.json()

        email = userinfo.get("email")
        name = userinfo.get("name")
        hd = userinfo.get("hd")  # domain

        if not email:
            flash("Google login didn't return an email.", "danger")
            return redirect(url_for("auth.login"))

        # 5️⃣ Domain check
        allowed = current_app.config.get("ALLOWED_DOMAIN")
        if allowed and allowed.lower() != email.split("@")[-1].lower():
            flash("Only institutional emails are allowed.", "danger")
            return redirect(url_for("auth.login"))

        # 6️⃣ Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                name=name or email.split("@")[0],
                email=email,
                role="student"
            )
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash("Logged in successfully.", "success")
        return redirect(url_for("main.dashboard"))

    except Exception as e:
        flash(f"Login failed: {e}", "danger")
        return redirect(url_for("auth.login"))


# -----------------------
# LOGOUT
# -----------------------

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect("/")
