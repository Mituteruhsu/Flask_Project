# routes/dashboard.py
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required, current_user

from sqlalchemy import inspect, text

from core.database import db
from forms.user_forms import UserForm
from forms.family_forms import FamilyForm
from forms.member_forms import FamilyMemberForm
from forms.invoice_forms import InvoiceForm
from database.models.user import User
from database.models.RBAC.role import Role
from database.models.subscription.plan import Plan
from database.models.family.family import Family
from database.models.family.family_member import FamilyMember, FamilyRole
from database.models.invoice import InvoiceRecord
from utils.decorators import admin_required, family_member_required, family_role_required, user_has_role
from werkzeug.security import generate_password_hash
from database.models.CRUD.services import UserService, RoleService, PermissionService, CapabilityService, FamilyMemberService, FamilyRoleService, FamilyService


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# 初始化 CRUD.Service 實例
user_service = UserService()
role_service = RoleService()
permission_service = PermissionService()
capability_service = CapabilityService()
family_member_service = FamilyMemberService()
family_role_service = FamilyRoleService()
family_service = FamilyService()

# ==========================================================
#  進入點：依角色自動導向 admin 或 user dashboard
# ==========================================================
@dashboard_bp.route("/")
@login_required
def index():
    # For admin
    if user_has_role("admin"):
        return redirect(url_for("dashboard.admin_index"))
    # For user
    return redirect(url_for("dashboard.user_index"))


# ==========================================================
#  管理者 Dashboard（平台層：全部使用者 / 家庭 / 方案）
# ==========================================================
@dashboard_bp.route("/admin")
@admin_required
def admin_index():
    """
    SaaS 系統管理者主頁：
    保留原本功能的同時，新增自動讀取並顯示全站所有 DB Table 數據的功能
    """
    # 1. 使用 SQLAlchemy Inspector 動態反射資料庫中所有的 Table 名稱
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    # 2. 取得網址帶入的 table 參數 (例如: /dashboard/admin?table=user)
    # 預設為 table 列表的第一個，若尚無 table 則為 None
    selected_table = request.args.get('table', table_names[0] if table_names else None)

    table_columns = []
    table_rows = []
    total_count = 0

    # 3. 針對選定的 Table 查詢欄位與資料列
    if selected_table and selected_table in table_names:
        # 讀取欄位名稱
        columns_info = inspector.get_columns(selected_table)
        table_columns = [col['name'] for col in columns_info]

        # 查詢 Table 內容 (加上 LIMIT 100 避免大資料卡死)
        query = text(f'SELECT * FROM "{selected_table}" LIMIT 100')
        result = db.session.execute(query)
        table_rows = [dict(row._mapping) for row in result]

        # 查詢總筆數
        count_query = text(f'SELECT COUNT(*) FROM "{selected_table}"')
        total_count = db.session.execute(count_query).scalar()

    # 渲染至你原本的 templates/dashboard/admin/index.html
    return render_template(
        'dashboard/admin/index.html',
        table_names=table_names,
        selected_table=selected_table,
        table_columns=table_columns,
        table_rows=table_rows,
        total_count=total_count
    )

@dashboard_bp.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.asc()).all()
    table_names = inspect(db.engine).get_table_names()
    return render_template("dashboard/admin/users.html", users=users, table_names=table_names)

@dashboard_bp.route("/admin/users/create", methods=["GET", "POST"])
@admin_required
def admin_create_user():
    form = UserForm()
    form.role_ids.choices = [(r.id, r.name) for r in Role.query.all()]

    if form.validate_on_submit():
        user = user_service.create(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data or "changeme123"),
        )
        user.roles = Role.query.filter(Role.id.in_(form.role_ids.data)).all()
        db.session.commit()
        flash(f"已建立使用者「{user.username}」", "success")
        return redirect(url_for("dashboard.admin_users"))

    return render_template("dashboard/admin/users_form.html", form=form, mode="create")


@dashboard_bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.role_ids.choices = [(r.id, r.name) for r in Role.query.all()]

    if request.method == "GET":
        form.role_ids.data = [r.id for r in user.roles]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.password.data:  # 有填才改密碼
            user.password_hash = generate_password_hash(form.password.data)
        user.roles = Role.query.filter(Role.id.in_(form.role_ids.data)).all()
        db.session.commit()
        flash(f"已更新使用者「{user.username}」", "success")
        return redirect(url_for("dashboard.admin_users"))

    return render_template("dashboard/admin/users_form.html", form=form, mode="edit", user=user)

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
    table_names = inspect(db.engine).get_table_names()   # 補這行
    return render_template("dashboard/admin/families.html", families=families, table_names=table_names)

@dashboard_bp.route("/admin/families/create", methods=["GET", "POST"])
@admin_required
def admin_create_family():
    form = FamilyForm()
    form.plan_id.choices = [(0, "未設定")] + [(p.id, p.name) for p in Plan.query.all()]

    if form.validate_on_submit():
        family_service.create(
            name=form.name.data,
            owner_user_id=current_user.id,
            plan_id=form.plan_id.data or None,
        )
        flash(f"已建立家庭「{form.name.data}」", "success")
        return redirect(url_for("dashboard.admin_families"))

    return render_template("dashboard/admin/family_form.html", form=form, mode="create")

@dashboard_bp.route("/admin/families/<int:family_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_family(family_id):
    family = Family.query.get_or_404(family_id)
    form = FamilyForm(obj=family)
    form.plan_id.choices = [(0, "未設定")] + [(p.id, p.name) for p in Plan.query.all()]

    if form.validate_on_submit():
        family.name = form.name.data
        family.plan_id = form.plan_id.data or None
        db.session.commit()
        flash(f"已更新家庭「{family.name}」", "success")
        return redirect(url_for("dashboard.admin_families"))

    return render_template("dashboard/admin/family_form.html", form=form, mode="edit", family=family)

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

# ---------- User：Invoice Edit（獨立頁面） ----------
@dashboard_bp.route("/user/invoices/<int:invoice_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("dashboard.user_index"))
    return render_template("dashboard/user/invoice_form.html", form=form, invoice=invoice)

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

@dashboard_bp.route("/user/members/add", methods=["GET", "POST"])
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
        return redirect(url_for("dashboard.user_members"))
    return render_template("dashboard/user/member_form.html", form=form, mode="create")

@dashboard_bp.route("/user/members/<int:member_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("dashboard.user_members"))

    return render_template("dashboard/user/member_form.html", form=form, mode="edit", target=target)

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
