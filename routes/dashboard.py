# routes/dashboard.py
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required, current_user

from core.database import db
from database.models.user import User
from database.models.family.family import Family
from database.models.family.family_member import FamilyMember, FamilyRole
from database.models.subscription.plan import Plan
from database.models.invoice import InvoiceRecord
from utils.decorators import admin_required, family_member_required, family_role_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# ==========================================================
#  進入點：依角色自動導向 admin 或 user dashboard
# ==========================================================
@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role == "admin":
        return redirect(url_for("dashboard.admin_index"))
    return redirect(url_for("dashboard.user_index"))


# ==========================================================
#  管理者 Dashboard（平台層：全部使用者 / 家庭 / 方案）
# ==========================================================
@dashboard_bp.route("/admin")
@admin_required
def admin_index():
    stats = {
        "user_count": User.query.count(),
        "family_count": Family.query.count(),
        "invoice_count": InvoiceRecord.query.filter_by(is_deleted=False).count(),
        "plan_count": Plan.query.count(),
    }
    return render_template("dashboard/admin/index.html", stats=stats)


@dashboard_bp.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.asc()).all()
    return render_template("dashboard/admin/users.html", users=users)


@dashboard_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("不能刪除自己的帳號", "warning")
        return redirect(url_for("dashboard.admin_users"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"已刪除使用者「{user.username}」", "success")
    return redirect(url_for("dashboard.admin_users"))


@dashboard_bp.route("/admin/families")
@admin_required
def admin_families():
    families = Family.query.order_by(Family.id.asc()).all()
    return render_template("dashboard/admin/families.html", families=families)


@dashboard_bp.route("/admin/families/<int:family_id>/delete", methods=["POST"])
@admin_required
def admin_delete_family(family_id):
    family = Family.query.get_or_404(family_id)
    db.session.delete(family)  # cascade="all, delete-orphan" 會一併刪除 FamilyMember
    db.session.commit()
    flash(f"已刪除家庭「{family.name}」", "success")
    return redirect(url_for("dashboard.admin_families"))


# ==========================================================
#  使用者 Dashboard（家庭層：自己的家庭 / 發票紀錄）
# ==========================================================
@dashboard_bp.route("/user")
@login_required
@family_member_required
def user_index():
    membership: FamilyMember = g.membership
    family = membership.family
    recent_invoices = (
        InvoiceRecord.query
        .join(User, InvoiceRecord.user_id == User.id)
        .join(FamilyMember, FamilyMember.user_id == User.id)
        .filter(FamilyMember.family_id == family.id, InvoiceRecord.is_deleted == False)
        .order_by(InvoiceRecord.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "dashboard/user/index.html",
        family=family,
        membership=membership,
        invoices=recent_invoices,
    )


@dashboard_bp.route("/user/invoices/<int:invoice_id>/delete", methods=["POST"])
@login_required
@family_member_required
def user_delete_invoice(invoice_id):
    """軟刪除：只標記 is_deleted，不真的從資料庫移除，可從垃圾桶復原"""
    membership: FamilyMember = g.membership
    invoice = InvoiceRecord.query.get_or_404(invoice_id)

    # 業務層權限判斷：直接複用 FamilyMember.can_edit_record
    # (parent 可刪全部，child 只能刪自己的，viewer 不能刪)
    if not membership.can_edit_record(invoice):
        abort(403)

    invoice.is_deleted = True
    invoice.deleted_at = datetime.now()
    db.session.commit()
    flash("發票紀錄已移至垃圾桶", "success")
    return redirect(url_for("dashboard.user_index"))


@dashboard_bp.route("/user/invoices/trash")
@login_required
@family_member_required
def user_invoice_trash():
    membership: FamilyMember = g.membership
    family = membership.family
    deleted_invoices = (
        InvoiceRecord.query
        .join(User, InvoiceRecord.user_id == User.id)
        .join(FamilyMember, FamilyMember.user_id == User.id)
        .filter(FamilyMember.family_id == family.id, InvoiceRecord.is_deleted == True)
        .order_by(InvoiceRecord.deleted_at.desc())
        .all()
    )
    return render_template(
        "dashboard/user/trash.html", invoices=deleted_invoices, membership=membership
    )


@dashboard_bp.route("/user/invoices/<int:invoice_id>/restore", methods=["POST"])
@login_required
@family_member_required
def user_restore_invoice(invoice_id):
    membership: FamilyMember = g.membership
    invoice = InvoiceRecord.query.get_or_404(invoice_id)

    if not membership.can_edit_record(invoice):
        abort(403)

    invoice.is_deleted = False
    invoice.deleted_at = None
    db.session.commit()
    flash("發票紀錄已復原", "success")
    return redirect(url_for("dashboard.user_invoice_trash"))


@dashboard_bp.route("/user/members")
@login_required
@family_member_required
def user_members():
    membership: FamilyMember = g.membership
    members = FamilyMember.query.filter_by(family_id=membership.family_id).all()
    return render_template(
        "dashboard/user/members.html", members=members, membership=membership
    )


@dashboard_bp.route("/user/members/<int:member_id>/delete", methods=["POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)  # 只有家長能移除成員
def user_delete_member(member_id):
    membership: FamilyMember = g.membership
    target = FamilyMember.query.get_or_404(member_id)

    if target.family_id != membership.family_id:
        abort(403)  # 不能動別的家庭
    if target.id == membership.id:
        flash("不能移除自己", "warning")
        return redirect(url_for("dashboard.user_members"))

    db.session.delete(target)
    db.session.commit()
    flash(f"已將「{target.nickname}」移出家庭", "success")
    return redirect(url_for("dashboard.user_members"))
