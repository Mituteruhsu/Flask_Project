# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from database.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # 已登入的人直接導去 dashboard，不用再看登入頁
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()  # username 或 email
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        # google 登入的帳號可能沒有 password_hash，這裡一併防呆
        if not user or not user.password_hash or not check_password_hash(user.password_hash, password):
            flash("帳號或密碼錯誤", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=remember)
        flash(f"歡迎回來，{user.username}！", "success")

        # 支援登入後導回原本想去的頁面（?next=...）
        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已成功登出", "info")
    return redirect(url_for("auth.login"))
