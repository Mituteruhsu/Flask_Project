# routes/dashboard_bp.py
from flask import Blueprint, redirect, url_for
from flask_login import login_required
from utils.decorators import user_has_role

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# ==========================================================
#  進入點：依角色自動導向 admin 或 user dashboard
# ==========================================================
@dashboard_bp.route("/")
@login_required
def index():
    # For admin
    if user_has_role("admin"):
        return redirect(url_for("admin.admin_index"))
    # For user
    return redirect(url_for("user.user_index"))
