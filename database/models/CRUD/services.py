from database.models.CRUD.base_service import BaseService
from database.models.user import User
from database.models.RBAC.role import Role
from database.models.RBAC.permission import Permission
from database.models.RBAC.capability import Capability
from database.models.family.family_member import FamilyMember, FamilyRole
from database.models.family.family import Family

# User 專用 Service，直接繼承所有 CRUD 功能
class UserService(BaseService):
    def __init__(self):
        super().__init__(User)

    # 如果需要特殊查詢（例如用 email 登入），再額外擴充專屬於 User 的方法
    def get_by_email(self, email):
        from database import db
        return db.session.scalar(db.select(User).filter_by(email=email))

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