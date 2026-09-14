# routes/user_bp.py
from flask import Blueprint, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required

from forms.invoice_forms import InvoiceForm
from database.models.family.family_member import FamilyMember
from database.services.CRUD.services import invoice_service

user_bp = Blueprint("user", __name__, url_prefix="/user")

# ==========================================================
#  使用者 Dashboard（家庭層：自己的家庭 / 發票紀錄）
# ==========================================================
# ---------- User：Index（首頁） ----------
@user_bp.route("/")
@login_required
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