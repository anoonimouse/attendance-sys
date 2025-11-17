import os
import pathlib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import dotenv_values

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    # -------------------------------
    # 1) Load .env file manually (WORKS ON WINDOWS)
    # -------------------------------
    root_path = pathlib.Path(__file__).parent.parent
    env_path = root_path / ".env"

    # Read .env as dictionary
    env_data = dotenv_values(env_path)

    print("Loaded .env from:", env_path)
    print("ENV CONTENTS:", env_data)

    # Inject each .env key into os.environ
    for key, value in env_data.items():
        os.environ[key] = value

    # -------------------------------
    # 2) Create Flask App
    # -------------------------------
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # -------------------------------
    # 3) Apply Config Values
    # -------------------------------
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # IMPORTANT: Make sure Google OAuth values load!
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")
    app.config["ALLOWED_DOMAIN"] = os.environ.get("ALLOWED_DOMAIN", "iitj.ac.in")

    # Debug print
    print("CLIENT_ID =", app.config["GOOGLE_CLIENT_ID"])
    print("CLIENT_SECRET =", app.config["GOOGLE_CLIENT_SECRET"])
    print("ALLOWED_DOMAIN =", app.config["ALLOWED_DOMAIN"])

    # -------------------------------
    # 4) Init Extensions
    # -------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    # -------------------------------
    # 5) Register Blueprints
    # -------------------------------
    from .auth import auth_bp
    from .main import main_bp
    from .teacher import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(teacher_bp, url_prefix="/teacher")

    # -------------------------------
    # 6) Create tables
    # -------------------------------
    with app.app_context():
        db.create_all()

    return app
