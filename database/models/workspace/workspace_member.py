# database/models/workspace/workspace_member.py
from enum import Enum
from core.database import db
from database.mixins import TimestampMixin, SoftDeleteMixin

class WorkspaceRole(Enum):
    PERSONAL = "personal"
    FAMILY = "family"
    BUSINESS = "business"
    TEAM = "team"

class WorkspaceMember(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'workspace_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    role = db.Column(db.Enum(WorkspaceRole), nullable=False)

    # 關聯到 User 和 Workspace
    user = db.relationship('User', backref=db.backref('workspace_memberships', lazy=True))
    workspace = db.relationship('Workspace', backref=db.backref('members', lazy=True))