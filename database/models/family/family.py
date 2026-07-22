# database/models/family/family.py
from core.database import db
from database.mixins import TimestampMixin

class Family(db.Model, TimestampMixin):
    __tablename__ = 'families'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)               # e.g. "許家記帳本"
    owner_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=True)

    plan = db.relationship("Plan", back_populates="families")
    members = db.relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")

    def has_capability(self, capability_name: str) -> bool:
        """檢查這個家庭目前的方案是否擁有某功能"""
        if not self.plan:
            return False
        return any(c.name == capability_name for c in self.plan.capabilities)

    def __repr__(self):
        return f"<Family {self.name}>"