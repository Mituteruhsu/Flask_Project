# database/models/CRUD/services.py
from database.models.CRUD.base_service import BaseService
from database.models.user import User
from database.models.RBAC.role import Role
from database.models.RBAC.permission import Permission
from database.models.RBAC.capability import Capability
from database.models.family.family_member import FamilyMember, FamilyRole
from database.models.family.family import Family
from database.models.invoice import InvoiceRecord
from core.database import db
from datetime import datetime

# User 專用 Service，直接繼承所有 CRUD 功能
class UserService(BaseService):
    def __init__(self):
        super().__init__(User)

    # 如果需要特殊查詢（例如用 email 登入），再額外擴充專屬於 User 的方法
    def get_by_email(self, email):        
        return db.session.scalar(db.select(User).filter_by(email=email))

    # 使用 BaseService 的 get_all 方法，傳入自訂的 stmt 這裡 "依照 id 升冪排序"
    def get_all_users(self):
        stmt = db.select(User).order_by(User.id.asc())
        return self.get_all(stmt=stmt)  

# Role 專用 Service
class RoleService(BaseService):
    def __init__(self):
        super().__init__(Role)

# Permission 專用 Service
class PermissionService(BaseService):
    def __init__(self):
        super().__init__(Permission)

# Capability 專用 Service
class CapabilityService(BaseService):   
    def __init__(self):
        super().__init__(Capability)

# FamilyMember 專用 Service
class FamilyMemberService(BaseService):
    def __init__(self):
        super().__init__(FamilyMember)

# FamilyRole 專用 Service
class FamilyRoleService(BaseService):
    def __init__(self):
        super().__init__(FamilyRole)

# Family 專用 Service
class FamilyService(BaseService):
    def __init__(self):
        super().__init__(Family)

# 發票專用服務層，繼承 BaseService 並擴充業務方法
class InvoiceService(BaseService):
    def __init__(self):
        super().__init__(InvoiceRecord)

    def get_family_invoices(self, family_id: int, is_deleted: bool = False, limit: int = None):
        """ 查詢特定家庭的發票紀錄 (封裝原本寫在路由內的三表 Join) """
        stmt = (
            db.select(InvoiceRecord)
            .join(User, InvoiceRecord.user_id == User.id)
            .join(FamilyMember, FamilyMember.user_id == User.id)
            .filter(FamilyMember.family_id == family_id, InvoiceRecord.is_deleted == is_deleted)
            .order_by(InvoiceRecord.created_at.desc())
        )
        if limit:
            stmt = stmt.limit(limit)
        return db.session.scalars(stmt).all()

    def update_invoice_from_form(self, invoice_id: int, form) -> InvoiceRecord:
        """ 處理發票表單更新並提交資料庫 """
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return None
        form.populate_obj(invoice)
        db.session.commit()
        return invoice

    def soft_delete(self, invoice_id: int) -> bool:
        """ 軟刪除：標記 is_deleted 並寫入刪除時間 """
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return False
        invoice.is_deleted = True
        invoice.deleted_at = datetime.now()
        db.session.commit()
        return True

    def restore_from_trash(self, invoice_id: int) -> bool:
        """ 還原：取消 is_deleted 標記 """
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return False
        invoice.is_deleted = False
        invoice.deleted_at = None
        db.session.commit()
        return True

# ============================
# 初始化 CRUD.Service 實例
# ============================
user_service = UserService()
role_service = RoleService()
permission_service = PermissionService()
capability_service = CapabilityService()
family_member_service = FamilyMemberService()
family_role_service = FamilyRoleService()
family_service = FamilyService()
invoice_service = InvoiceService()
