# database/models/RBAC/permission.py
from core.database import db

class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # e.g. "user:manage", "invoice:view_all"
    description = db.Column(db.String(255), nullable=True)

    # 多對多：反向對應 Role.permissions
    roles = db.relationship("Role", secondary="role_permissions", back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.name}>"