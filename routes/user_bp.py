# routes/user_bp.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required, current_user

from forms.member_forms import FamilyMemberForm
from forms.invoice_forms import InvoiceForm
from database.models.family.family_member import FamilyMember, FamilyRole
from utils.decorators import family_member_required, family_role_required
from database.models.CRUD.services import family_member_service, invoice_service

user_bp = Blueprint("user", __name__, url_prefix="/user")

# ==========================================================
#  使用者 Dashboard（家庭層：自己的家庭 / 發票紀錄）
# ==========================================================
# ---------- User：Index（首頁） ----------
@user_bp.route("/")
@login_required
@family_member_required
def user_index():
    """ 記帳主頁：完全改用 invoice_service 撈取該家庭最近 10 筆發票 """
    membership: FamilyMember = g.membership
    family = membership.family
    recent_invoices = invoice_service.get_family_invoices(
        family_id=family.id,
        is_deleted=False,
        limit=10
    )
    
    return render_template(
        "dashboard/user/index.html",
        family=family,
        membership=membership,
        invoices=recent_invoices,
    )

# ---------- User：Invoice Edit（更新） ----------
@user_bp.route("/invoices/<int:invoice_id>/edit", methods=["GET", "POST"])
@login_required
@family_member_required
def user_edit_invoice(invoice_id):
    """ 編輯發票 """
    membership: FamilyMember = g.membership    
    # 使用 invoice_service 獲取發票
    invoice = invoice_service.get_by_id(invoice_id)
    if not invoice:
        abort(404)        
    if not membership.can_edit_record(invoice):
        abort(403)
    form = InvoiceForm(obj=invoice)
    if form.validate_on_submit():
        # 將更新行為交給服務層，避免路由直接調用 db.session.commit()
        invoice_service.update_invoice_from_form(invoice_id, form)
        flash("發票資料已更新", "success")
        return redirect(url_for("user.user_index"))        
    return render_template("dashboard/invoice_form.html", form=form, invoice=invoice)

# ---------- User：Invoice Delete（軟刪除）----------
@user_bp.route("/invoices/<int:invoice_id>/delete", methods=["POST"])
@login_required
@family_member_required
def user_delete_invoice(invoice_id):
    """ 軟刪除：is_deleted 標記為已刪除，不真的從資料庫移除，可從垃圾桶復原 """
    membership: FamilyMember = g.membership
    invoice = invoice_service.get_by_id(invoice_id)
    if not invoice:
        abort(404)
        
    if not membership.can_edit_record(invoice):
        abort(403)
        
    # 💡 呼叫服務層執行軟刪除
    invoice_service.soft_delete(invoice_id)
    flash("發票紀錄已移至垃圾桶", "success")
    return redirect(url_for("user.user_index"))

# ---------- User：Invoice Trash（垃圾桶）----------
@user_bp.route("/invoices/trash")
@login_required
@family_member_required
def user_invoice_trash():
    """ 垃圾桶列表：呼叫服務層獲取已刪除數據 """
    membership: FamilyMember = g.membership
    family = membership.family
    deleted_invoices = invoice_service.get_family_invoices(
        family_id=family.id,
        is_deleted=True
    )
    
    return render_template(
        "dashboard/user/trash.html", invoices=deleted_invoices, membership=membership
    )

# ---------- User：Invoice Restore（復原）----------
@user_bp.route("/invoices/<int:invoice_id>/restore", methods=["POST"])
@login_required
@family_member_required
def user_restore_invoice(invoice_id):
    """ 從垃圾桶還原發票 """
    membership: FamilyMember = g.membership    
    invoice = invoice_service.get_by_id(invoice_id)
    if not invoice:
        abort(404)
    if not membership.can_edit_record(invoice):
        abort(403)
    invoice_service.restore_from_trash(invoice_id)
    flash("發票紀錄已復原", "success")
    return redirect(url_for("user.user_invoice_trash"))

# ---------- User：Family Members（家庭成員列表）----------
@user_bp.route("/members")
@login_required
@family_member_required
def user_members():
    """ 顯示家庭成員列表 """
    membership: FamilyMember = g.membership
    members = family_member_service.filter_by(family_id=membership.family_id)
    return render_template(
        "dashboard/user/members.html", members=members, membership=membership
    )

# --------- User：Add Member（新增家庭成員）----------
@user_bp.route("/members/add", methods=["GET", "POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def user_add_member():
    """ 新增家庭成員 """
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

# --------- User：Edit Member（編輯家庭成員）----------
@user_bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def user_edit_member(member_id):
    """ 編輯家庭成員 """
    membership: FamilyMember = g.membership
    target = family_member_service.get_by_id(member_id)
    if not target or target.family_id != membership.family_id:
        abort(403)        
    form = FamilyMemberForm(obj=target)
    if request.method == "GET":
        form.family_role.data = target.family_role.value
    if form.validate_on_submit():
        # 💡 使用 BaseService 的 update 方法，避免在路由直接給屬性賦值與 commit
        family_member_service.update(
            target.id,
            nickname=form.nickname.data,
            family_role=FamilyRole(form.family_role.data),
            is_active=form.is_active.data
        )
        flash("已更新成員資料", "success")
        return redirect(url_for("user.user_members"))
        
    return render_template("dashboard/user/member_form.html", form=form, mode="edit", target=target)

# --------- User：Delete Member（刪除家庭成員）----------
@user_bp.route("/members/<int:member_id>/delete", methods=["POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def user_delete_member(member_id):
    """ 移除家庭成員 """
    membership: FamilyMember = g.membership
    target = family_member_service.get_by_id(member_id)
    if not target or target.family_id != membership.family_id:
        abort(403)  # 不能動別的家庭     
    if target.id == membership.id:
        flash("不能移除自己", "warning")
        return redirect(url_for("user.user_members"))
    family_member_service.delete(target.id)
    flash(f"已將「{target.nickname}」移出家庭", "success")
    return redirect(url_for("user.user_members"))