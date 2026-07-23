# database/models/RBAC/capability.py
from core.database import db

class Capability(db.Model):
    """系統功能開關，綁定在 Plan 上，不綁定在 Role 上"""
    __tablename__ = 'capabilities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)   # e.g. "ai_category", "google_sheet_export"
    description = db.Column(db.String(255), nullable=True)
    
    # 多對多：反向對應 Plan.capabilities
    # (原本這裡沒有這個關聯，Plan 那邊的 back_populates="plans" 會找不到對應屬性而在
    #  mapper configure 時報錯，所以這裡是必要的修正，不是額外加功能)
    plans = db.relationship("Plan", secondary="plan_capabilities", back_populates="capabilities")

    def __repr__(self):
        return f"<Capability {self.name}>"