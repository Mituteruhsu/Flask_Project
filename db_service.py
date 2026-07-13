from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text, inspect
from datetime import datetime
from werkzeug.security import generate_password_hash

# ==================== 
# 定義 SQLAlchemy 基類
# ====================
class Base(DeclarativeBase):
    # 這裡可以放一些共用的欄位或方法，例如 created_at、updated_at 會在繼承時自動加入到子類別中
    # created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    pass

# ====================
#   初始化 db 實例
# ====================
db = SQLAlchemy(model_class=Base)
# 放到資料表定義中，讓[所有]資料表都繼承 Base，並自動擁有 created_at 與 updated_at 欄位
# 例如: class InvoiceRecord(db.Model) 透過繼承 Base 會在資料表中自動擁有 created_at 與 updated_at 欄位
# Base 也可以 pass，透過 Mixin 的方式來加減共用欄位，可以更靈活控制 

# ====================
#       Mixin
# ====================
# 放到資料表定義中，讓[各別]資料表都繼承 Mixin，並自動擁有 created_at 與 updated_at 欄位
# 例如: class InvoiceRecord(db.Model, TimestampMixin)

# --------------------
#   RBAC 權限常數定義
class Permission:
    """ 系統權限位元遮罩（未來可做精細控制） """
    READ = 1          # 0001 (一般檢視、看歷史紀錄)
    UPLOAD = 2        # 0010 (上傳發票、執行 OCR/QR 辨識)
    SYNC = 4          # 0100 (手動或自動同步至 Google Sheet)
    ADMIN = 8         # 1000 (管理後台 CRUD、管理使用者權限)

class Role:
    """ 系統角色與權限映射 """
    MAP = {
        'user': Permission.READ | Permission.UPLOAD | Permission.SYNC, # 一般使用者
        'auditor': Permission.READ,                                    # 稽核員（只能看不能改）
        'admin': Permission.READ | Permission.UPLOAD | Permission.SYNC | Permission.ADMIN # 超級管理員
    }
# --------------------
# 負責時間戳記
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

# 負責軟刪除功能
class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

# ====================
#      資料表定義
# ====================
# 使用者資料表
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default='user')
    google_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    google_credentials: Mapped[str] = mapped_column(String(2000), nullable=True)
    target_sheet_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # 一對多關聯：一個使用者擁有多筆發票紀錄
    invoices: Mapped[list["InvoiceRecord"]] = relationship("InvoiceRecord", backref="owner", lazy=True)

# 發票紀錄資料表
class InvoiceRecord(db.Model, TimestampMixin):
    __tablename__ = 'invoice_records'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- 您要求的發票細緻欄位 ---
    invoice_num: Mapped[str] = mapped_column(String(50), nullable=False)                       # 發票號碼
    invoice_date: Mapped[str] = mapped_column(String(20), nullable=True)                       # 開立日期
    random_code: Mapped[str] = mapped_column(String(10), nullable=True)                        # 隨機碼
    sales_amount: Mapped[str] = mapped_column(String(50), nullable=True)                       # 銷售額
    total_amount: Mapped[str] = mapped_column(String(50), nullable=True)                       # 推算總金額
    buyer_invoice_num: Mapped[str] = mapped_column(String(20), nullable=True)                  # 買方統編
    seller_invoice_num: Mapped[str] = mapped_column(String(20), nullable=True)                 # 賣方統編
    aes_encode: Mapped[str] = mapped_column(String(100), nullable=True)                        # AES加密
    after77_data: Mapped[str] = mapped_column(String(500), nullable=True)                      # 77個字元後的資料
    free_usage: Mapped[str] = mapped_column(String(100), nullable=True)                        # 營業人使用區
    item_count: Mapped[str] = mapped_column(String(10), nullable=True)                         # 品項筆數
    total_item_count: Mapped[str] = mapped_column(String(10), nullable=True)                   # 品項總筆數
    code_type: Mapped[str] = mapped_column(String(10), nullable=True)                          # 編碼類型
    items_detail: Mapped[str] = mapped_column(Text, nullable=True)                             # 品項明細 (可能很長，用 Text)
    item_quantity: Mapped[str] = mapped_column(String(50), nullable=True)                      # 品項數量
    items_price: Mapped[str] = mapped_column(String(50), nullable=True)                        # 品項單價
    method: Mapped[str] = mapped_column(String(50), default="QR Code")                         # 辨識方法
    
    # --- 系統管理與第三方整合必備欄位 ---
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)               # 本地資料庫建立時間
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)       # 隸屬的使用者 ID
    is_synced_to_sheet: Mapped[bool] = mapped_column(Boolean, default=False)                   # 是否同步至 Google Sheet
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)                       # 同步時間

# ==================== 
# 資料庫比對與初始化服務
# ====================
class DBService:
    @staticmethod
    def init_db(app):
        """ 全自動多表規格比對與初始化機制 """
        db.init_app(app)
        with app.app_context():
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