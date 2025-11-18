from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from .models import User, Room, AttendanceSlot, AttendanceRecord
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
        query = query.filter(User.email.ilike(f"%{q}%") | User.name.ilike(f"%{q}%"))
    users = query.all()
    return render_template("admin/users.html", users=users, q=q)


@admin_bp.route("/user/<int:uid>/promote", methods=["POST"])
@login_required
@admin_required
def promote(uid):
    u = User.query.get_or_404(uid)
    if u.role == "teacher":
        return jsonify({"ok": False, "msg": "User is already a teacher"}), 400
    u.promote_to_teacher()
    db.session.commit()
    return jsonify({"ok": True, "msg": f"{u.email} promoted to teacher"})


@admin_bp.route("/user/<int:uid>/demote", methods=["POST"])
@login_required
@admin_required
def demote(uid):
    u = User.query.get_or_404(uid)
    if u.role == "admin":
        return jsonify({"ok": False, "msg": "Cannot demote admin"}), 403
    if u.role == "student":
        return jsonify({"ok": False, "msg": "User is already a student"}), 400
    u.demote_to_student()
    db.session.commit()
    return jsonify({"ok": True, "msg": f"{u.email} demoted to student"})


@admin_bp.route("/user/<int:uid>/ban", methods=["POST"])
@login_required
@admin_required
def ban(uid):
    u = User.query.get_or_404(uid)
    if u.is_banned:
        return jsonify({"ok": False, "msg": "User is already banned"}), 400
    u.ban()
    db.session.commit()
    return jsonify({"ok": True, "msg": f"{u.email} has been banned"})


@admin_bp.route("/user/<int:uid>/unban", methods=["POST"])
@login_required
@admin_required
def unban(uid):
    u = User.query.get_or_404(uid)
    if not u.is_banned:
        return jsonify({"ok": False, "msg": "User is not banned"}), 400
    u.unban()
    db.session.commit()
    return jsonify({"ok": True, "msg": f"{u.email} has been unbanned"})


@admin_bp.route("/route-tester")
@login_required
@admin_required
def route_tester():
    """Super admin only - shows all registered routes"""
    if current_user.email not in current_app.config["ADMINS"]:
        flash("Super admin access required", "danger")
        return redirect(url_for("admin.index"))
    
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": ", ".join(rule.methods - {"HEAD", "OPTIONS"}),
            "path": str(rule)
        })
    
    routes.sort(key=lambda x: x["path"])
    
    return render_template("admin/route_tester.html", routes=routes)