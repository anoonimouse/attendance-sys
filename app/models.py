from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import gen_salt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200), unique=True, nullable=False)
    role = db.Column(db.String(20), default="student")  # student, teacher, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    device_fingerprint = db.Column(db.String(256), nullable=True)  # store last fingerprint

    def is_teacher(self):
        return self.role in ("teacher", "admin")

    def is_admin(self):
        return self.role == "admin"

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AttendanceSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"))
    opened_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    pin_code = db.Column(db.String(6), nullable=True)    # 5-digit numeric string
    qr_token = db.Column(db.String(64), nullable=True)   # token embedded in QR
    require_pin = db.Column(db.Boolean, default=True)    # whether marking requires PIN

class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey("attendance_slot.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fingerprint = db.Column(db.String(256), nullable=True)
    method = db.Column(db.String(20), default="pin")  # pin | qr

from . import login_manager
@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))
