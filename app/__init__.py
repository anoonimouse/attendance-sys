# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    # -------------------------
    # Load .env
    # -------------------------
    base_dir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(base_dir, "..", ".env"))

    print("Loaded .env from:", os.path.join(base_dir, "..", ".env"))

    app = Flask(__name__)

    # -------------------------
    # Flask Config
    # -------------------------
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # OAuth Config
    app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")
    app.config["ALLOWED_DOMAIN"] = os.getenv("ALLOWED_DOMAIN", "").lower()

    # Admin list (super admins)
    admins_raw = os.getenv("ADMINS", "")
    admins_list = [email.strip().lower() for email in admins_raw.split(",") if email.strip()]
    app.config["ADMINS"] = admins_list

    print("Super Admins:", app.config["ADMINS"])


    # -------------------------
    # Init extensions
    # -------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # -------------------------
    # User Loader
    # -------------------------
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------
    # Register Blueprints
    # -------------------------
    from .auth import auth_bp, init_oauth
    from .main import main_bp
    from .admin import admin_bp  # (You will add this file later)

    # VERY IMPORTANT: init OAuth after app is created
    init_oauth(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    # -------------------------
    # Create DB Tables
    # -------------------------
    with app.app_context():
        try:
            db.create_all()
            print("Database tables checked/created.")
        except Exception as e:
            print("Error creating tables:", e)

    return app
