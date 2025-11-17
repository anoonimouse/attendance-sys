from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from .models import Room, AttendanceSlot, AttendanceRecord, User
from . import db
from datetime import datetime
import random, secrets
import qrcode
import io
import base64

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    now = datetime.utcnow()
    active = AttendanceSlot.query.filter(
        AttendanceSlot.is_active==True,
        AttendanceSlot.start_time <= now,
        AttendanceSlot.end_time >= now
    ).order_by(AttendanceSlot.start_time.desc()).first()
    # summary stats (simple)
    total_sessions = AttendanceSlot.query.count()
    attended_count = AttendanceRecord.query.filter_by(student_id=current_user.id).count()
    attendance_rate = 0
    if total_sessions:
        attendance_rate = round((attended_count / total_sessions) * 100, 1)
    rooms = Room.query.all()
    return render_template("student/dashboard.html",
                           user=current_user,
                           active=active,
                           total_sessions=total_sessions,
                           attended=attended_count,
                           attendance_rate=attendance_rate,
                           rooms=rooms)

@main_bp.route("/attendance/mark", methods=["POST"])
@login_required
def mark_attendance():
    """
    Expect JSON:
    { fingerprint: <visitorId>, pin: <optional>, qr_token: <optional>, method: "pin"|"qr" }
    """
    data = request.get_json() or {}
    fingerprint = data.get("fingerprint")
    method = data.get("method", "pin")
    now = datetime.utcnow()

    # find active slot
    slot = AttendanceSlot.query.filter(
        AttendanceSlot.is_active==True,
        AttendanceSlot.start_time <= now,
        AttendanceSlot.end_time >= now
    ).order_by(AttendanceSlot.start_time.desc()).first()

    if not slot:
        return jsonify({"ok":False, "msg":"No active session"}), 400

    # If slot requires pin and method is pin:
    if method == "pin" and slot.require_pin:
        pin = data.get("pin")
        if not pin or slot.pin_code != pin:
            return jsonify({"ok":False, "msg":"Invalid PIN"}), 403

    # If method is qr, verify token
    if method == "qr":
        token = data.get("qr_token")
        if not token or slot.qr_token != token:
            return jsonify({"ok":False, "msg":"Invalid QR token"}), 403

    # check duplicate
    exists = AttendanceRecord.query.filter_by(slot_id=slot.id, student_id=current_user.id).first()
    if exists:
        return jsonify({"ok":False, "msg":"Already marked"}), 200

    # fingerprint verification: if user.device_fingerprint exists, ensure it matches
    if current_user.device_fingerprint:
        # small tolerance: if mismatch, require confirmation — here we reject outright
        if fingerprint and fingerprint != current_user.device_fingerprint:
            return jsonify({"ok":False, "msg":"Device fingerprint mismatch"}), 403
    else:
        # store their fingerprint on first successful mark
        if fingerprint:
            current_user.device_fingerprint = fingerprint
            db.session.add(current_user)

    rec = AttendanceRecord(slot_id=slot.id, student_id=current_user.id, timestamp=now, fingerprint=fingerprint, method=method)
    db.session.add(rec)
    db.session.commit()
    return jsonify({"ok":True, "msg":"Attendance recorded", "timestamp": rec.timestamp.isoformat()})

@main_bp.route("/attendance/history")
@login_required
def history():
    records = AttendanceRecord.query.filter_by(student_id=current_user.id).order_by(AttendanceRecord.timestamp.desc()).all()
    return render_template("student/history.html", records=records)

@main_bp.route("/slot/<int:slot_id>/qr.png")
@login_required
def slot_qr(slot_id):
    """Return PNG of a QR for a slot (only for teachers but kept simple)"""
    slot = AttendanceSlot.query.get_or_404(slot_id)
    # build URL containing token — students scanning should hit a simple mark URL or use mobile to open UI
    url = url_for("main.qr_mark", slot_id=slot.id, token=slot.qr_token, _external=True)
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return current_app.response_class(buf.getvalue(), mimetype="image/png")

@main_bp.route("/qr/mark")
@login_required
def qr_mark():
    """
    A convenience page for when students scan QR and open in browser.
    It shows a button that will call the JS marking endpoint with qr_token.
    """
    slot_id = request.args.get("slot_id")
    token = request.args.get("token")
    return render_template("student/qr_mark.html", slot_id=slot_id, token=token)
