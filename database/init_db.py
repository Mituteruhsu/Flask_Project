from core.database import db
from database.sync import DatabaseSync
from database.seed import DatabaseSeeder

# ==================== 
# 資料庫比對與初始化服務
# ====================
class DBService:
    @staticmethod
    def init_db(app):
        """ 全自動多表規格比對與初始化機制 """
        db.init_app(app)
        with app.app_context():
            DatabaseSync._sync_datatable()
            DatabaseSeeder._seed_admin_user()
            # 加入其他初始化流程，也都放在這裡: 以下範例
            # DatabaseSeeder._seed_roles()
            # DatabaseSeeder._seed_permissions()
            # DatabaseSeeder._seed_admin_user()
            # DatabaseSeeder._seed_system_settings()
            