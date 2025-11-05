# from datetime import datetime
# from passlib.hash import pbkdf2_sha256 as hasher
# from db_connect import db

# class User(db.Model):
#     __tablename__ = 'auf_users'
#     slno = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(128), unique=True, nullable=False)
#     password_hash = db.Column(db.String(256), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False, nullable=False)
#     must_reset = db.Column(db.Boolean, default=False)
#     reset_requested = db.Column(db.Boolean, default=False)
#     last_login_time = db.Column(db.DateTime)
#     reset_password_time = db.Column(db.DateTime)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

#     def set_password(self, plaintext):
#         self.password_hash = hasher.hash(plaintext)

#     def check_password(self, plaintext):
#         return hasher.verify(plaintext, self.password_hash)

#     def to_dict(self):
#         return {
#             "slno": self.slno,
#             "username": self.username,
#             "is_admin": self.is_admin,
#             "must_reset": self.must_reset,
#             "reset_requested": self.reset_requested,
#             "last_login_time": self.last_login_time.isoformat() if self.last_login_time else None,
#             "reset_password_time": self.reset_password_time.isoformat() if self.reset_password_time else None,
#             "created_at": self.created_at.isoformat() if self.created_at else None
#         }
