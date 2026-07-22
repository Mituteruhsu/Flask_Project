# database/models/family/family_member.py
import enum
from core.database import db
from database.mixins import TimestampMixin

class FamilyRole(enum.Enum):
    PARENT = "parent"   # 家長：可管理成員、編輯/刪除所有帳目、設定方案
    CHILD = "child"      # 小孩：只能新增/編輯自己的帳目
    VIEWER = "viewer"    # 唯讀家人：只能查看，不能異動

class FamilyMember(db.Model, TimestampMixin):
    __tablename__ = 'family_members'
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    nickname = db.Column(db.String(50), nullable=False)             # 家庭內顯示用暱稱，避免多個小孩本名混淆
    family_role = db.Column(db.Enum(FamilyRole), default=FamilyRole.CHILD, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    family = db.relationship("Family", back_populates="members")
    user = db.relationship("User", backref="family_memberships")

    __table_args__ = (
        db.UniqueConstraint("family_id", "user_id", name="uq_family_user"),
    )

    def can_edit_record(self, record) -> bool:
        """業務層權限判斷：家長可編輯全部，小孩只能編輯自己的"""
        if self.family_role == FamilyRole.PARENT:
            return True
        if self.family_role == FamilyRole.CHILD:
            return record.owner_id == self.user_id
        return False  # VIEWER

    def __repr__(self):
        return f"<FamilyMember {self.nickname} ({self.family_role.value})>"