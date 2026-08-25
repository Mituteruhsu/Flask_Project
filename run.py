import os
import sqlite3
from flask import Flask
from flask_wtf import CSRFProtect
from core.database import db
from core.login import init_login_manager
from services.image_service import ImageService
from services.qr_service import QRService
from services.ocr_service import OCRService
from database.init_db import DBService
from database.models.invoice import InvoiceRecord
from routes.index_bp import index_bp
from routes.auth_bp import auth_bp
from routes.dashboard_bp import dashboard_bp
from routes.admin_bp import admin_bp
from routes.user_bp import user_bp

# ===========================
#       Flask App
# ===========================
app = Flask(__name__)

# 隨機產生一個 SECRET_KEY，確保 CSRF 保護的安全性
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)
# print(f"Flask App 啟動中，使用的 SECRET_KEY 為: {app.config['SECRET_KEY']}")

# 設定 Jsonify 不要自動排序 key，保持原本的順序
app.json.sort_keys = False
# 使用項目目錄下的 uploads 資料夾（解決 Windows /tmp 路徑問題）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 確保資料夾存在
DB_PATH = os.path.join(PROJECT_DIR, 'invoices.db')
# ===== ↑↑↑↑↑ Flask App ↑↑↑↑↑ =====

# ========================
#       Database
# ========================
# 程式啟動時，立即初始化或檢查資料庫
# 配置 Flask-SQLAlchemy 連線路徑
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 核心：初始化 db 並與 app 綁定，防呆資料庫初始化，自動檢查並建立所有資料表
DBService.init_db(app)
# ===== ↑↑↑↑↑ Database ↑↑↑↑↑ =====

# ===========================
#       Blueprints
# ===========================
# 藉由建立 Blueprint 來模組化路由，方便管理不同功能的路由群組
# Login / Auth
init_login_manager(app)
app.register_blueprint(index_bp)
app.register_blueprint(auth_bp)
# 前端路由 與 API 串接
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)
# ===== ↑↑↑↑↑ Blueprints ↑↑↑↑↑ =====

if __name__ == '__main__':
    # app.run(debug=True)
    # host='0.0.0.0' 代表監聽所有網路介面
    # port=8000 可以自訂埠號（預設是 5000）
    app.run(host='0.0.0.0', port=8000, debug=True)
