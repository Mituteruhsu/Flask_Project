# utils/decorators.py
"""
權限裝飾器：
- admin_required        平台管理者專用（User.role == 'admin'）
- family_member_required 必須屬於某個家庭才能進入 /dashboard/user
- family_role_required   限制家庭內角色（例如只有 parent 能刪除成員）
"""
from functools import wraps
from flask import abort, g
from flask_login import current_user
from database.models.family.family_member import FamilyMember, FamilyRole


def admin_required(view_func):
    """僅平台管理者 (User.role == 'admin') 可存取"""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if getattr(current_user, "role", None) != "admin":
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped


def family_member_required(view_func):
    """
    必須是某個家庭的成員才能進入。
    會把當下使用者在該家庭的 FamilyMember 記錄放到 g.membership，
    方便後續在 view 或 template 裡判斷權限（例如 parent / child / viewer）。

    注意：這裡先取「使用者的第一個家庭」作為 MVP 版本；
    多家庭情境下建議之後改成 session 記錄「目前使用中的 family_id」。
    """
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        membership = (
            FamilyMember.query
            .filter_by(user_id=current_user.id, is_active=True)
            .first()
        )
        if membership is None:
            abort(403)  # 尚未加入任何家庭

        g.membership = membership
        return view_func(*args, **kwargs)
    return wrapped


def family_role_required(*allowed_roles: FamilyRole):
    """
    限制家庭內角色，需搭配 family_member_required 使用（要先有 g.membership）。
    用法：@family_role_required(FamilyRole.PARENT)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            membership = getattr(g, "membership", None)
            if membership is None:
                abort(403)
            if membership.family_role not in allowed_roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
