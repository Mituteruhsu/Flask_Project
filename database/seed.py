from werkzeug.security import generate_password_hash
from core.database import db
from database.models.user import User

# =======================
#       預設資料建立
# =======================
class DatabaseSeeder:
    # 預設 user 資料建立 admin
    @staticmethod
    def seed_admin_user():
        """ 檢查 users 資料表，若無人則自動建立第一個 admin """
        print("檢查 users 資料表，若無人則自動建立第一個 admin")
        try:
            admin_exists = User.query.filter_by(role='admin').first()
            if not admin_exists:
                # 安全地產生密碼雜湊
                hashed_password = generate_password_hash("admin123")
                default_admin = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=hashed_password,
                    role="admin"
                )
                db.session.add(default_admin)
                db.session.commit()
                print("🎉 預設管理員建立成功！(帳號: admin / 密碼: admin123)")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 建立預設管理員帳號失敗: {e}")
    
    def seed_roles():
        pass  # 之後加入 roles 資料表的預設資料

    def seed_permissions():
        pass  # 之後加入 permissions 資料表的預設資料

    def seed_capabilities():
        pass  # 之後加入 capabilities 資料表的預設資料

    def seed_invoice_categories():
        pass  # 之後加入 invoice_categories 資料表的預設資料

    def seed_family_members():
        pass  # 之後加入 family_members 資料表的預設資料

    def seed_system_settings():
        pass  # 之後加入 system_settings 資料表的預設資料

    def system_settings():
        pass  # 之後加入 system_settings 資料表的預設資料