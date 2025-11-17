from flask import Blueprint, redirect, url_for, session, flash, current_app
from authlib.integrations.flask_client import OAuth
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
import secrets

auth_bp = Blueprint("auth", __name__)
oauth = OAuth()

@auth_bp.record_once
def on_load(state):
    oauth.init_app(state.app)
    oauth.register(
        name="google",
        client_id=state.app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=state.app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"}
    )

@auth_bp.route("/login")
def login():
    # Generate nonce
    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce

    redirect_uri = url_for("auth.callback", _external=True)

    return oauth.google.authorize_redirect(
        redirect_uri,
        nonce=nonce
    )

@auth_bp.route("/auth/callback")
def callback():
    token = oauth.google.authorize_access_token()

    # Retrieve stored nonce
    nonce = session.get("nonce")
    if not nonce:
        flash("Login session expired. Try again.", "error")
        return redirect(url_for("main.index"))

    # Parse + verify ID token with nonce
    userinfo = oauth.google.parse_id_token(token, nonce=nonce)
    if not userinfo:
        flash("Failed to verify Google login.", "error")
        return redirect(url_for("main.index"))

    email = userinfo.get("email")
    domain = email.split("@")[-1]
    allowed = current_app.config.get("ALLOWED_DOMAIN")

    if allowed.lower() != domain.lower():
        flash(f"Only @{allowed} emails allowed.", "error")
        return redirect(url_for("main.index"))

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            name=userinfo.get("name"),
            email=email,
            role="student"
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    session.pop("nonce", None)

    return redirect(url_for("main.dashboard"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("main.index"))
