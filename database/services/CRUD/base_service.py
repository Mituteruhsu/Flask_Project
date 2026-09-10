# database/models/CRUD/base_service.py
from core.database import db
from datetime import datetime

class BaseService:
    def __init__(self, model):
        self.model = model  # 綁定具體的 db.Model

    # --- Create ---
    def create(self, **kwargs):
        """新增一筆紀錄"""
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    # --- Read ---
    def get_by_id(self, record_id):
        """根據 ID 查詢單筆"""
        # SQLAlchemy 2.0+ 建議用法：db.session.get()
        return db.session.get(self.model, record_id)

    def get_all(self, stmt=None):
        """查詢所有紀錄，stmt 讓 services.py 可以傳入自訂的查詢條件（例如排序、過濾等）"""
        if stmt is None:
            stmt = db.select(self.model) # 這裡單純查詢所有紀錄，沒有條件
        return db.session.scalars(stmt).all()

    def filter_by(self, **kwargs):
        """條件查詢（多筆）"""
        return db.session.scalars(db.select(self.model).filter_by(**kwargs)).all()

    # --- Update ---
    def update(self, record_id, **kwargs):
        """根據 ID 更新紀錄"""
        instance = self.get_by_id(record_id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.session.commit()
        return instance

    # --- Delete ---
    def delete(self, record_id):
        """根據 ID 刪除紀錄"""
        instance = self.get_by_id(record_id)
        if not instance:
            return False
        db.session.delete(instance)
        db.session.commit()
        return True

    # --- Soft Delete ---
    def soft_delete(self, record_id):
        """
        軟刪除：model 必須有 is_deleted 欄位（繼承 SoftDeleteMixin）。
        沒有的話丟出明確錯誤，避免默默失敗。
        """
        instance = self.get_by_id(record_id)
        if not instance:
            return None
        if not hasattr(instance, "is_deleted"):
            raise AttributeError(f"{self.model.__name__} 沒有 is_deleted 欄位，無法軟刪除")
        instance.is_deleted = True
        if hasattr(instance, "deleted_at"):
            instance.deleted_at = datetime.now()
        db.session.commit()
        return instance

    def restore(self, record_id):
        """復原軟刪除"""
        instance = self.get_by_id(record_id)
        if not instance:
            return None
        instance.is_deleted = False
        if hasattr(instance, "deleted_at"):
            instance.deleted_at = None
        db.session.commit()
        return instance