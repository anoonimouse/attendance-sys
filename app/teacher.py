from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from .models import Room, AttendanceSlot, AttendanceRecord, User
from . import db
from datetime import datetime, timedelta
import random, secrets

teacher_bp = Blueprint("teacher", __name__)

@teacher_bp.before_request
def ensure_teacher():
    if not current_user.is_authenticated or not current_user.is_teacher():
        return ("", 403)

@teacher_bp.route("/rooms")
def rooms():
    rooms = Room.query.order_by(Room.created_at.desc()).all()
    return render_template("teacher/rooms.html", rooms=rooms)

@teacher_bp.route("/rooms/create", methods=["GET","POST"])
def create_room():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Name required", "error")
            return redirect(url_for("teacher.create_room"))
        r = Room(name=name, created_by=current_user.id)
        db.session.add(r)
        db.session.commit()
        flash("Room created", "success")
        return redirect(url_for("teacher.rooms"))
    return render_template("teacher/create_room.html")

@teacher_bp.route("/slots/open", methods=["GET","POST"])
def open_slot():
    rooms = Room.query.all()
    if request.method == "POST":
        room_id = int(request.form.get("room_id"))
        duration_min = int(request.form.get("duration", "5"))
        require_pin = request.form.get("require_pin") == "on"
        start = datetime.utcnow()
        end = start + timedelta(minutes=duration_min)
        pin_code = None
        qr_token = secrets.token_urlsafe(32)
        if require_pin:
            pin_code = f"{random.randint(0,99999):05d}"
        slot = AttendanceSlot(room_id=room_id, opened_by=current_user.id,
                              start_time=start, end_time=end, is_active=True,
                              pin_code=pin_code, qr_token=qr_token, require_pin=require_pin)
        db.session.add(slot)
        db.session.commit()
        flash("Slot opened!", "success")
        return redirect(url_for("teacher.rooms"))
    return render_template("teacher/open_slot.html", rooms=rooms)

@teacher_bp.route("/slots/close/<int:slot_id>", methods=["POST"])
def close_slot(slot_id):
    slot = AttendanceSlot.query.get_or_404(slot_id)
    slot.is_active = False
    db.session.commit()
    flash("Slot closed", "info")
    return redirect(url_for("teacher.rooms"))

@teacher_bp.route("/slot/<int:slot_id>/live")
def slot_live(slot_id):
    slot = AttendanceSlot.query.get_or_404(slot_id)
    # list of records (most recent 50)
    recs = AttendanceRecord.query.filter_by(slot_id=slot.id).order_by(AttendanceRecord.timestamp.desc()).limit(200).all()
    # build simple JSON
    out = []
    for r in recs:
        u = User.query.get(r.student_id)
        out.append({
            "name": u.name,
            "email": u.email,
            "timestamp": r.timestamp.isoformat()
        })
    return jsonify({"ok":True, "records": out})

@teacher_bp.route("/slot/<int:slot_id>/export")
def slot_export(slot_id):
    slot = AttendanceSlot.query.get_or_404(slot_id)
    import csv, io
    recs = db.session.query(AttendanceRecord, User).join(User, User.id==AttendanceRecord.student_id).filter(AttendanceRecord.slot_id==slot_id).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Student Name","Email","Timestamp","Method"])
    for rec, user in recs:
        cw.writerow([user.name, user.email, rec.timestamp.isoformat(), rec.method])
    output = si.getvalue()
    return current_app.response_class(output, mimetype="text/csv", headers={"Content-Disposition":f"attachment;filename=attendance_slot_{slot_id}.csv"})
