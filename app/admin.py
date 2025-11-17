from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from .models import User
from . import db

admin_bp = Blueprint("admin", __name__, template_folder="templates/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not (current_user.role == "admin" or current_user.email in current_app.config["ADMINS"]):
            flash("Admin access required", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/")
@login_required
@admin_required
def index():
    total_users = User.query.count()
    total_students = User.query.filter_by(role="student").count()
    total_teachers = User.query.filter_by(role="teacher").count()
    banned_count = User.query.filter_by(is_banned=True).count()
    latest = User.query.order_by(User.created_at.desc()).limit(6).all()

    return render_template("admin/dashboard.html",
                           total_users=total_users,
                           total_students=total_students,
                           total_teachers=total_teachers,
                           banned_count=banned_count,
                           latest=latest)


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    q = request.args.get("q", "").strip()
    query = User.query.order_by(User.created_at.desc())
    if q:
        query = query.filter(User.email.ilike(f"%{q}%"))
    users = query.all()
    return render_template("admin/users.html", users=users, q=q)


def _get(uid):
    return User.query.get_or_404(uid)


@admin_bp.route("/user/<int:uid>/promote", methods=["POST"])
@login_required
@admin_required
def promote(uid):
    u = _get(uid)
    u.promote_to_teacher()
    db.session.commit()
    return jsonify({"ok": True})

@admin_bp.route("/promote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.role == "teacher":
        return jsonify({"ok": False, "msg": "User is already a teacher."}), 400

    user.role = "teacher"
    db.session.commit()

    return jsonify({"ok": True, "msg": f"{user.email} promoted to teacher"})

@admin_bp.route("/demote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.role == "student":
        return jsonify({"ok": False, "msg": "User is already a student."}), 400

    user.role = "student"
    db.session.commit()

    return jsonify({"ok": True, "msg": f"{user.email} demoted to student"})


@admin_bp.route("/user/<int:uid>/demote", methods=["POST"])
@login_required
@admin_required
def demote(uid):
    u = _get(uid)
    if u.role == "admin":
        return jsonify({"ok": False, "msg": "Cannot demote admin"}), 403
    u.demote_to_student()
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.route("/user/<int:uid>/ban", methods=["POST"])
@login_required
@admin_required
def ban(uid):
    u = _get(uid)
    u.ban()
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.route("/user/<int:uid>/unban", methods=["POST"])
@login_required
@admin_required
def unban(uid):
    u = _get(uid)
    u.unban()
    db.session.commit()
    return jsonify({"ok": True})
