from sqlalchemy import  inspect
from werkzeug.security import generate_password_hash
from core.database import db
from models.database_models.user import User

# ==================== 
# 資料庫比對與初始化服務
# ====================
class DBService:
    @staticmethod
    def init_db(app):
        """ 全自動多表規格比對與初始化機制 """
        db.init_app(app)
        with app.app_context():
            DBService._sync_database()
            DBService._seed_admin_user()

    @staticmethod
    def _sync_database():
        """ 核心：自動比對資料表結構，若有任何不符則自動重建 """
        inspector = inspect(db.engine)
        need_rebuild = False
        
        # 1. 自動抓取我們在 models.py 裡定義的所有資料表名稱
        defined_tables = db.metadata.tables.keys()
        
        for table_name in defined_tables:
            # 檢查實體資料庫是否有這個資料表，沒有就代表規格變更，需要重建
            if not inspector.has_table(table_name):
                print(f"⚠️ 偵測到資料庫缺少新定義的資料表: [{table_name}]")
                need_rebuild = True
                break
                
            # 2. 如果資料表存在，自動抓取實體資料庫「當前現有」的所有欄位名稱
            db_columns = {col['name'] for col in inspector.get_columns(table_name)}
            
            # 3. 自動抓取 models.py 裡定義該 Table「應該要有」的所有欄位名稱
            model_columns = set(db.metadata.tables[table_name].columns.keys())
            
            # 4. 進行集合比對，只要任何欄位對不起來（無論是少欄位還是型態變更），就判定需要重建
            if not model_columns.issubset(db_columns):
                missing = model_columns - db_columns
                print(f"⚠️ 資料表 [{table_name}] 規格不符！缺少欄位: {missing}")
                need_rebuild = True
                break

        # 5. 執行最終防呆決策
        if need_rebuild:
            print("🔄 正在執行安全重置：清除舊結構並自動依據 models.py 建立全新全表規格...")
            db.drop_all()   # 安全清除主系統所有資料表
            db.create_all() # 一口氣全新建立所有符合規格的最新資料表
            print("🎉 全專案資料表結構已自動同步並建立完畢！")
        else:
            # 如果檔案完全不存在（第一次執行）
            if not inspector.get_table_names():
                print("🔍 偵測到全新環境，正在初始化所有資料表...")
                db.create_all()
                print("🎉 資料表全新建立成功。")
            else:
                print(" 資料庫多表結構完整性檢查通過，所有 Table 與欄位完全一致。")

    @staticmethod
    def _seed_admin_user():
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