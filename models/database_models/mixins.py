from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Boolean
from datetime import datetime
# ====================
#       Mixin
# ====================
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