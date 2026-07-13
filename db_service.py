from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text
from datetime import datetime

# -------------------- 
# 定義 SQLAlchemy 基類
# --------------------
class Base(DeclarativeBase):
    # 這裡可以放一些共用的欄位或方法，例如 created_at、updated_at 會在繼承時自動加入到子類別中
    # created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    # updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    pass

# --------------------
#   初始化 db 實例
# --------------------
db = SQLAlchemy(model_class=Base)
# 放到資料表定義中，讓[所有]資料表都繼承 Base，並自動擁有 created_at 與 updated_at 欄位
# 例如: class InvoiceRecord(db.Model) 透過繼承 Base 會在資料表中自動擁有 created_at 與 updated_at 欄位
# Base 也可以 pass，透過 Mixin 的方式來加減共用欄位，可以更靈活控制 

# --------------------
#       Mixin
# --------------------
# 放到資料表定義中，讓[各別]資料表都繼承 Mixin，並自動擁有 created_at 與 updated_at 欄位
# 例如: class InvoiceRecord(db.Model, TimestampMixin)

# 負責時間戳記
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

# 負責軟刪除功能
class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

# --------------------
#      資料表定義
# --------------------
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
