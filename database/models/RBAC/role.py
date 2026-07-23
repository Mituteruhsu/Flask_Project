# database/models/RBAC/role.py
from core.database import db

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # super_admin / admin / user
    description = db.Column(db.String(255), nullable=True)

    # 多對多：一個 Role 有多個 Permission，一個 Permission 也能給多個 Role 使用
    permissions = db.relationship("Permission", secondary="role_permissions", back_populates="roles")

    def __repr__(self):
        return f"<Role {self.name}>"