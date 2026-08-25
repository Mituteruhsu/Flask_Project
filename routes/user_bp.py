# routes/user_bp.py
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required, current_user

from core.database import db
from forms.member_forms import FamilyMemberForm
from forms.invoice_forms import InvoiceForm
from database.models.user import User
from database.models.family.family_member import FamilyMember, FamilyRole
from database.models.invoice import InvoiceRecord
from utils.decorators import family_member_required, family_role_required, user_has_role
from database.models.CRUD.services import FamilyMemberService


user_bp = Blueprint("user", __name__, url_prefix="/user")

# 初始化 CRUD.Service 實例
family_member_service = FamilyMemberService()

# ==========================================================
#  使用者 Dashboard（家庭層：自己的家庭 / 發票紀錄）
# ==========================================================
@user_bp.route("/")
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

# ---------- User：Invoice Edit（獨立頁面） ----------
@user_bp.route("/invoices/<int:invoice_id>/edit", methods=["GET", "POST"])
@login_required
@family_member_required
def user_edit_invoice(invoice_id):
    membership: FamilyMember = g.membership
    invoice = InvoiceRecord.query.get_or_404(invoice_id)

    if not membership.can_edit_record(invoice):
        abort(403)

    form = InvoiceForm(obj=invoice)
    if form.validate_on_submit():
        form.populate_obj(invoice)
        db.session.commit()
        flash("發票資料已更新", "success")
        return redirect(url_for("user.user_index"))
    return render_template("dashboard/invoice_form.html", form=form, invoice=invoice)

@user_bp.route("/invoices/<int:invoice_id>/delete", methods=["POST"])
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
    return redirect(url_for("user.user_index"))


@user_bp.route("/invoices/trash")
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


@user_bp.route("/invoices/<int:invoice_id>/restore", methods=["POST"])
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
    return redirect(url_for("user.user_invoice_trash"))


@user_bp.route("/members")
@login_required
@family_member_required
def user_members():
    membership: FamilyMember = g.membership
    members = FamilyMember.query.filter_by(family_id=membership.family_id).all()
    return render_template(
        "dashboard/user/members.html", members=members, membership=membership
    )

@user_bp.route("/members/add", methods=["GET", "POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def user_add_member():
    membership: FamilyMember = g.membership
    form = FamilyMemberForm()

    if form.validate_on_submit():
        family_member_service.create(
            family_id=membership.family_id,
            user_id=current_user.id,  # 實務上這裡應改成「邀請」流程去綁定其他 user_id
            nickname=form.nickname.data,
            family_role=form.family_role.data,
            is_active=form.is_active.data,
        )
        flash("已新增家庭成員", "success")
        return redirect(url_for("user.user_members"))
    return render_template("dashboard/user/member_form.html", form=form, mode="create")

@user_bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def user_edit_member(member_id):
    membership: FamilyMember = g.membership
    target = FamilyMember.query.get_or_404(member_id)
    if target.family_id != membership.family_id:
        abort(403)

    form = FamilyMemberForm(obj=target)
    if request.method == "GET":
        form.family_role.data = target.family_role.value

    if form.validate_on_submit():
        target.nickname = form.nickname.data
        target.family_role = FamilyRole(form.family_role.data)
        target.is_active = form.is_active.data
        db.session.commit()
        flash("已更新成員資料", "success")
        return redirect(url_for("user.user_members"))

    return render_template("dashboard/user/member_form.html", form=form, mode="edit", target=target)

@user_bp.route("/members/<int:member_id>/delete", methods=["POST"])
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
        return redirect(url_for("user.user_members"))

    db.session.delete(target)
    db.session.commit()
    flash(f"已將「{target.nickname}」移出家庭", "success")
    return redirect(url_for("user.user_members"))
