from datetime import datetime, timedelta
from flask_login import UserMixin
from . import db


# ---------------------------
# USER MODEL
# ---------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)

    role = db.Column(db.String(50), default="student")   # student | teacher | admin
    is_banned = db.Column(db.Boolean, default=False)

    device_fingerprint = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_active_at = db.Column(db.DateTime)

    # --- relationships ---
    attendance_records = db.relationship("AttendanceRecord", backref="student", lazy=True)

    # --- helper functions ---
    def is_admin(self):
        return self.role == "admin"

    def is_teacher(self):
        return self.role == "teacher"

    def is_student(self):
        return self.role == "student"

    def promote_to_teacher(self):
        self.role = "teacher"

    def demote_to_student(self):
        self.role = "student"

    def make_admin(self):
        self.role = "admin"

    def ban(self):
        self.is_banned = True

    def unban(self):
        self.is_banned = False

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# ---------------------------
# ROOM MODEL
# ---------------------------
class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    slots = db.relationship("AttendanceSlot", backref="room", lazy=True)

    def __repr__(self):
        return f"<Room {self.name}>"


# ---------------------------
# ATTENDANCE SLOT MODEL
# ---------------------------
class AttendanceSlot(db.Model):
    __tablename__ = "attendance_slots"

    id = db.Column(db.Integer, primary_key=True)

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    opened_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=5))

    is_active = db.Column(db.Boolean, default=True)

    # PIN system
    require_pin = db.Column(db.Boolean, default=False)
    pin_code = db.Column(db.String(10))

    # QR token
    qr_token = db.Column(db.String(64))

    attendance_records = db.relationship("AttendanceRecord", backref="slot", lazy=True)

    def __repr__(self):
        return f"<Slot {self.id} Room={self.room_id} Active={self.is_active}>"


# ---------------------------
# ATTENDANCE RECORD MODEL
# ---------------------------
class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(db.Integer, primary_key=True)

    slot_id = db.Column(db.Integer, db.ForeignKey("attendance_slots.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fingerprint = db.Column(db.String(500))
    method = db.Column(db.String(20))  # pin or qr

    def __repr__(self):
        return f"<AttendanceRecord user={self.student_id} slot={self.slot_id}>"
