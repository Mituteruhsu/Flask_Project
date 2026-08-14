# database/models/CRUD/CRUD_service.py
from core.database import db

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

    def get_all(self):
        """查詢所有紀錄"""
        return db.session.scalars(db.select(self.model)).all()

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