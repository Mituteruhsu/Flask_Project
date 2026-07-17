from core.database import db
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from models.database_models.invoice import InvoiceRecord

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