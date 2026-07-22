# database/models/subscription/plan.py
from core.database import db

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # free / pro / family_plus
    price = db.Column(db.Integer, default=0)
    max_members = db.Column(db.Integer, default=4)                 # 免費方案家庭成員上限
    description = db.Column(db.String(255), nullable=True)

    capabilities = db.relationship("Capability", secondary="plan_capabilities", back_populates="plans")
    families = db.relationship("Family", back_populates="plan")

    def __repr__(self):
        return f"<Plan {self.name}>"