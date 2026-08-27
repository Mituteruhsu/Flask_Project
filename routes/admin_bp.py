# routes/admin_bp.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import current_user
from utils.decorators import admin_required
from werkzeug.security import generate_password_hash

from database.models.user import User
from database.models.RBAC.role import Role
from database.models.family.family import Family
from database.models.subscription.plan import Plan
from database.models.CRUD.services import user_service, family_service
from core.database import db
from sqlalchemy import inspect, text

from forms.user_forms import UserForm
from forms.family_forms import FamilyForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ==========================================================
#  管理者 Dashboard（平台層：全部使用者 / 家庭 / 方案）
# ==========================================================
@admin_bp.route("/")
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

@admin_bp.route("/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.id.asc()).all()
    table_names = inspect(db.engine).get_table_names()
    return render_template("dashboard/admin/users.html", users=users, table_names=table_names)

@admin_bp.route("/users/create", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_users"))

    return render_template("dashboard/admin/users_form.html", form=form, mode="create")


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_users"))

    return render_template("dashboard/admin/users_form.html", form=form, mode="edit", user=user)

@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    if user_id == current_user.id:
        flash("不能刪除自己的帳號", "warning")
        return redirect(url_for("admin.admin_users"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"已刪除使用者「{user.username}」", "success")
    return redirect(url_for("admin.admin_users"))


@admin_bp.route("/families")
@admin_required
def admin_families():
    families = Family.query.order_by(Family.id.asc()).all()
    table_names = inspect(db.engine).get_table_names()   # 補這行
    return render_template("dashboard/admin/families.html", families=families, table_names=table_names)

@admin_bp.route("/families/create", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_families"))

    return render_template("dashboard/admin/family_form.html", form=form, mode="create")

@admin_bp.route("/families/<int:family_id>/edit", methods=["GET", "POST"])
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
        return redirect(url_for("admin.admin_families"))

    return render_template("dashboard/admin/family_form.html", form=form, mode="edit", family=family)

@admin_bp.route("/families/<int:family_id>/delete", methods=["POST"])
@admin_required
def admin_delete_family(family_id):
    family = Family.query.get_or_404(family_id)
    db.session.delete(family)  # cascade="all, delete-orphan" 會一併刪除 FamilyMember
    db.session.commit()
    flash(f"已刪除家庭「{family.name}」", "success")
    return redirect(url_for("admin.admin_families"))
