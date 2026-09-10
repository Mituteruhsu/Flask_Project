# database/models/workspace/workspace.py
from core.database import db
from database.mixins import TimestampMixin

class Workspace(TimestampMixin, db.Model):
    __tablename__ = "workspaces"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=True)

    plan = db.relationship("Plan", back_populates="workspaces")
    members = db.relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")

    def has_capability(self, capability_name: str) -> bool:
            """檢查這個家庭目前的方案是否擁有某功能"""
            if not self.plan:
                return False
            return any(c.name == capability_name for c in self.plan.capabilities)
    
    def __repr__(self):
        return f"<Family {self.name}>"
