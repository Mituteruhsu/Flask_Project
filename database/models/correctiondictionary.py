from core.database import db
from database.mixins import TimestampMixin, SoftDeleteMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean

# ====================
#      資料表定義
# ====================
# 修正字典資料表
class CorrectionDictionary(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'correction_dictionaries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)    # 變體/錯字
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)                    # 標準名稱
    category: Mapped[str] = mapped_column(String(50), default='general')                        # 類別 (merchant/item)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- 軟刪除欄位由 SoftDeleteMixin 提供：is_deleted / deleted_at ---