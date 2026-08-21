# routes/index.py
from flask import Blueprint, redirect, url_for
from flask_login import current_user

index_bp = Blueprint("index", __name__, url_prefix="/")

@index_bp.route("/", methods=["GET"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))
