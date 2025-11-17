from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from .models import Room, AttendanceSlot, AttendanceRecord, User
from . import db
from datetime import datetime
import qrcode
import io

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------
# PUBLIC ROUTE
# ---------------------------------------------------------------------
@main_bp.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------
# STUDENT DASHBOARD
# ---------------------------------------------------------------------
@main_bp.route("/dashboard")
@login_required
def dashboard():
    now = datetime.utcnow()

    active = AttendanceSlot.query.filter(
        AttendanceSlot.is_active == True,
        AttendanceSlot.start_time <= now,
        AttendanceSlot.end_time >= now
    ).order_by(AttendanceSlot.start_time.desc()).first()

    # student stats
    total_sessions = AttendanceSlot.query.count()
    attended_count = AttendanceRecord.query.filter_by(student_id=current_user.id).count()

    attendance_rate = round((attended_count / total_sessions) * 100, 1) if total_sessions else 0

    rooms = Room.query.all()

    return render_template(
        "student/dashboard.html",
        user=current_user,
        active=active,
        total_sessions=total_sessions,
        attended=attended_count,
        attendance_rate=attendance_rate,
        rooms=rooms
    )


# ---------------------------------------------------------------------
# STUDENT: MARK ATTENDANCE
# ---------------------------------------------------------------------
@main_bp.route("/attendance/mark", methods=["POST"])
@login_required
def mark_attendance():
    """
    Expect JSON:
    {
        fingerprint: <visitorId>,
        pin: <optional>,
        qr_token: <optional>,
        method: "pin" | "qr"
    }
    """
    data = request.get_json() or {}
    fingerprint = data.get("fingerprint")
    method = data.get("method", "pin")
    now = datetime.utcnow()

    # active slot lookup
    slot = AttendanceSlot.query.filter(
        AttendanceSlot.is_active == True,
        AttendanceSlot.start_time <= now,
        AttendanceSlot.end_time >= now
    ).order_by(AttendanceSlot.start_time.desc()).first()

    if not slot:
        return jsonify({"ok": False, "msg": "No active session"}), 400

    # PIN Method
    if method == "pin" and slot.require_pin:
        pin = data.get("pin")
        if not pin or pin != slot.pin_code:
            return jsonify({"ok": False, "msg": "Invalid PIN"}), 403

    # QR Method
    if method == "qr":
        token = data.get("qr_token")
        if not token or token != slot.qr_token:
            return jsonify({"ok": False, "msg": "Invalid QR token"}), 403

    # Check duplicate
    exists = AttendanceRecord.query.filter_by(slot_id=slot.id, student_id=current_user.id).first()
    if exists:
        return jsonify({"ok": False, "msg": "Already marked"}), 200

    # Fingerprint check
    if current_user.device_fingerprint:
        if fingerprint and fingerprint != current_user.device_fingerprint:
            return jsonify({"ok": False, "msg": "Device fingerprint mismatch"}), 403
    else:
        # First attendance: save device fingerprint
        if fingerprint:
            current_user.device_fingerprint = fingerprint
            db.session.add(current_user)

    # Save attendance
    rec = AttendanceRecord(
        slot_id=slot.id,
        student_id=current_user.id,
        timestamp=now,
        fingerprint=fingerprint,
        method=method
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({"ok": True, "msg": "Attendance recorded", "timestamp": rec.timestamp.isoformat()})


# ---------------------------------------------------------------------
# STUDENT: ATTENDANCE HISTORY
# ---------------------------------------------------------------------
@main_bp.route("/attendance/history")
@login_required
def history():
    records = AttendanceRecord.query.filter_by(
        student_id=current_user.id
    ).order_by(AttendanceRecord.timestamp.desc()).all()

    return render_template("student/history.html", records=records)


# ---------------------------------------------------------------------
# TEACHER-ONLY: GENERATE QR PNG
# ---------------------------------------------------------------------
@main_bp.route("/slot/<int:slot_id>/qr.png")
@login_required
def slot_qr(slot_id):
    """
    Return a PNG QR code for the given slot.
    SECURITY: Only teachers/admin should access this.
    """

    # 🔐 TEACHER ONLY
    if not current_user.is_teacher():
        return "Unauthorized", 403

    slot = AttendanceSlot.query.get_or_404(slot_id)

    # Build QR URL for student device
    qr_url = url_for(
        "main.qr_mark",
        slot_id=slot.id,
        token=slot.qr_token,
        _external=True
    )

    img = qrcode.make(qr_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return current_app.response_class(buf.getvalue(), mimetype="image/png")


# ---------------------------------------------------------------------
# STUDENT: QR MARKING PAGE
# ---------------------------------------------------------------------
@main_bp.route("/qr/mark")
@login_required
def qr_mark():
    """
    Page shown after a student scans the QR.
    Student clicks "Mark Attendance" → Calls /attendance/mark using method="qr".
    """
    slot_id = request.args.get("slot_id")
    token = request.args.get("token")

    return render_template("student/qr_mark.html", slot_id=slot_id, token=token)
