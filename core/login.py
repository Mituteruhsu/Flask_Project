# core/login.py
"""
Flask-Login 初始化
在 run.py 裡呼叫 init_login_manager(app) 即可。
"""
from flask_login import LoginManager
from database.models.user import User

login_manager = LoginManager()
login_manager.login_view = "auth.login"        # 未登入時自動導向登入頁
login_manager.login_message = "請先登入才能使用此功能"
login_manager.login_message_category = "warning"


def init_login_manager(app):
    login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))
