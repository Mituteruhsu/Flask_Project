# database/models/RBAC/plan_capability.py
from core.database import db

# Plan <-> Capability 多對多關聯表
plan_capabilities = db.Table(
    "plan_capabilities",
    db.Column("plan_id", db.Integer, db.ForeignKey("plans.id"), primary_key=True),
    db.Column("capability_id", db.Integer, db.ForeignKey("capabilities.id"), primary_key=True),
)