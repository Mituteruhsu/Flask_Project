# database/models/RBAC/capability.py
from core.database import db

class Capability(db.Model):
    """系統功能開關，綁定在 Plan 上，不綁定在 Role 上"""
    __tablename__ = 'capabilities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # e.g. "ai_category", "google_sheet_export"
    description = db.Column(db.String(255), nullable=True)

    plans = db.relationship("Plan", secondary="plan_capabilities", back_populates="capabilities")

    def __repr__(self):
        return f"<Capability {self.name}>"