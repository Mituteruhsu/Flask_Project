from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Boolean
from datetime import datetime
# ====================
#       Mixin
# ====================
# 屬於：資料表能力，非核心初始化。
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
