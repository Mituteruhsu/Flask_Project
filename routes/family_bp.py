# routes/user_bp.py
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required, current_user

from forms.member_forms import FamilyMemberForm
from database.models.family.family_member import FamilyMember, FamilyRole
from utils.decorators import family_member_required, family_role_required
from database.services.CRUD.services import family_member_service

family_bp = Blueprint("family", __name__, url_prefix="/family")

# ==========================================================
#  家庭使用者 Dashboard（家庭層：自己的家庭 / 發票紀錄）
# ==========================================================

# ---------- User：Family Members（家庭成員列表）----------
@family_bp.route("/members")
@login_required
@family_member_required
def family_members():
    """ 顯示家庭成員列表 """
    membership: FamilyMember = g.membership
    members = family_member_service.filter_by(family_id=membership.family_id)
    return render_template(
        "dashboard/user/members.html", members=members, membership=membership
    )

# --------- User：Add Member（新增家庭成員）----------
@family_bp.route("/members/add", methods=["GET", "POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def family_add_member():
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
@family_bp.route("/members/<int:member_id>/edit", methods=["GET", "POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def family_edit_member(member_id):
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
@family_bp.route("/members/<int:member_id>/delete", methods=["POST"])
@login_required
@family_member_required
@family_role_required(FamilyRole.PARENT)
def family_delete_member(member_id):
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