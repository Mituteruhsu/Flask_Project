from models.database_models.Base import db
from models.database_models.mixins import TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text
from datetime import datetime

# ====================
#      資料表定義
# ====================
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