from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

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