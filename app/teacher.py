from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from .models import Room, AttendanceSlot, AttendanceRecord, User
from . import db
from datetime import datetime, timedelta
import random, secrets

teacher_bp = Blueprint("teacher", __name__)

print("✓ Teacher blueprint created")

@teacher_bp.before_request
def ensure_teacher():
    """Ensure only teachers and admins can access teacher routes"""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not (current_user.is_teacher() or current_user.is_admin()):
        flash("Teacher access required", "danger")
        return redirect(url_for("main.dashboard"))


# ---------------------------------------------------------------------
# TEACHER DASHBOARD
# ---------------------------------------------------------------------
@teacher_bp.route("/dashboard")
def dashboard():
    """Teacher dashboard with stats and active sessions"""
    total_rooms = Room.query.filter_by(created_by=current_user.id).count()
    
    # Get all students
    total_students = User.query.filter_by(role="student").count()
    
    # Calculate average attendance across all sessions
    all_slots = AttendanceSlot.query.join(Room).filter(Room.created_by == current_user.id).all()
    total_attendance = 0
    total_possible = 0
    
    for slot in all_slots:
        attended = AttendanceRecord.query.filter_by(slot_id=slot.id).count()
        total_attendance += attended
        total_possible += total_students
    
    avg_attendance = round((total_attendance / total_possible) * 100, 1) if total_possible else 0
    
    # Get active session
    now = datetime.utcnow()
    active_session = AttendanceSlot.query.filter(
        AttendanceSlot.is_active == True,
        AttendanceSlot.start_time <= now,
        AttendanceSlot.end_time >= now
    ).join(Room).filter(Room.created_by == current_user.id).first()
    
    # Get recent sessions
    recent_sessions = AttendanceSlot.query.join(Room).filter(
        Room.created_by == current_user.id
    ).order_by(AttendanceSlot.start_time.desc()).limit(5).all()
    
    return render_template(
        "teacher/dashboard.html",
        total_rooms=total_rooms,
        total_students=total_students,
        avg_attendance=avg_attendance,
        active_session=active_session,
        recent_sessions=recent_sessions
    )


# ---------------------------------------------------------------------
# ROOMS MANAGEMENT
# ---------------------------------------------------------------------
@teacher_bp.route("/rooms")
def rooms():
    rooms = Room.query.filter_by(created_by=current_user.id).order_by(Room.created_at.desc()).all()
    return render_template("teacher/rooms.html", rooms=rooms)


@teacher_bp.route("/rooms/create", methods=["GET","POST"])
def create_room():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Room name required", "error")
            return redirect(url_for("teacher.create_room"))
        r = Room(name=name, created_by=current_user.id)
        db.session.add(r)
        db.session.commit()
        flash("Room created successfully", "success")
        return redirect(url_for("teacher.rooms"))
    return render_template("teacher/create_room.html")


# ---------------------------------------------------------------------
# ATTENDANCE SLOT MANAGEMENT
# ---------------------------------------------------------------------
@teacher_bp.route("/slots/open", methods=["GET","POST"])
def open_slot():
    rooms = Room.query.filter_by(created_by=current_user.id).all()
    
    if not rooms:
        flash("Please create a room first", "warning")
        return redirect(url_for("teacher.create_room"))
    
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
        
        slot = AttendanceSlot(
            room_id=room_id, 
            opened_by=current_user.id,
            start_time=start, 
            end_time=end, 
            is_active=True,
            pin_code=pin_code, 
            qr_token=qr_token, 
            require_pin=require_pin
        )
        db.session.add(slot)
        db.session.commit()
        
        flash(f"Attendance slot opened! {'PIN: ' + pin_code if pin_code else ''}", "success")
        return redirect(url_for("teacher.slot_live", slot_id=slot.id))
    
    return render_template("teacher/open_slot.html", rooms=rooms)


@teacher_bp.route("/slots/close/<int:slot_id>", methods=["POST"])
def close_slot(slot_id):
    slot = AttendanceSlot.query.get_or_404(slot_id)
    
    # Verify this teacher owns the room
    room = Room.query.get(slot.room_id)
    if room.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"ok": False, "msg": "Unauthorized"}), 403
    
    slot.is_active = False
    db.session.commit()
    
    return jsonify({"ok": True, "msg": "Slot closed"})


# ---------------------------------------------------------------------
# LIVE ATTENDANCE FEED
# ---------------------------------------------------------------------
@teacher_bp.route("/slot/<int:slot_id>/live")
def slot_live(slot_id):
    """Live attendance monitoring page"""
    slot = AttendanceSlot.query.get_or_404(slot_id)
    
    # Verify ownership
    room = Room.query.get(slot.room_id)
    if room.created_by != current_user.id and not current_user.is_admin():
        flash("Unauthorized", "danger")
        return redirect(url_for("teacher.dashboard"))
    
    return render_template("teacher/slot_live.html", slot=slot, room=room)


@teacher_bp.route("/slot/<int:slot_id>/feed")
def slot_feed(slot_id):
    """JSON feed for live attendance updates"""
    slot = AttendanceSlot.query.get_or_404(slot_id)
    
    # Verify ownership
    room = Room.query.get(slot.room_id)
    if room.created_by != current_user.id and not current_user.is_admin():
        return jsonify({"ok": False, "msg": "Unauthorized"}), 403
    
    # Get attendance records
    recs = AttendanceRecord.query.filter_by(slot_id=slot.id).order_by(
        AttendanceRecord.timestamp.desc()
    ).limit(200).all()
    
    # Build JSON response
    out = []
    for r in recs:
        u = User.query.get(r.student_id)
        out.append({
            "name": u.name,
            "email": u.email,
            "timestamp": r.timestamp.isoformat(),
            "method": r.method
        })
    
    return jsonify({
        "ok": True, 
        "records": out,
        "total": len(out),
        "is_active": slot.is_active
    })


# ---------------------------------------------------------------------
# EXPORT ATTENDANCE
# ---------------------------------------------------------------------
@teacher_bp.route("/slot/<int:slot_id>/export")
def slot_export(slot_id):
    """Export attendance to CSV"""
    slot = AttendanceSlot.query.get_or_404(slot_id)
    
    # Verify ownership
    room = Room.query.get(slot.room_id)
    if room.created_by != current_user.id and not current_user.is_admin():
        flash("Unauthorized", "danger")
        return redirect(url_for("teacher.dashboard"))
    
    import csv, io
    
    recs = db.session.query(AttendanceRecord, User).join(
        User, User.id == AttendanceRecord.student_id
    ).filter(AttendanceRecord.slot_id == slot_id).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["Student Name", "Email", "Timestamp", "Method"])
    
    for rec, user in recs:
        cw.writerow([user.name, user.email, rec.timestamp.isoformat(), rec.method])
    
    output = si.getvalue()
    
    return current_app.response_class(
        output, 
        mimetype="text/csv", 
        headers={
            "Content-Disposition": f"attachment;filename=attendance_slot_{slot_id}.csv"
        }
    )