# database/models/RBAC/user_roles.py
from core.database import db

# User <-> Role 多對多關聯表
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
)