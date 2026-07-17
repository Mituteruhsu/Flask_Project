'''
預期 V4
project/
│
├── core/
│   │
│   ├── __init__.py
│   ├── database.py
│   └── config.py
│
├── database/
│   ├── __init__.py
│   ├── init_db.py
│   ├── schema_sync.py
│   ├── seed.py
│   ├── mixins.py
│   ├── permissions.py
│   │
│   └── models/
│       ├── __init__.py
│       ├── user.py
│       └── invoice.py
│
├── models/
│   └── data_models/
│       └── qr_model.py
│
└── services/
    │
    ├── image_service.py
    ├── ocr_service.py
    └── qr_service.py

database/
├── __init__.py         # 對外入口
├── init_db.py          # 初始化資料庫
├── inspector.py        # 比對 Table 結構
├── seeder.py           # 建立預設資料（Admin、Role、System Settings...）
├── creator.py          # 建立/重建資料表 create_all, drop_all
├── migration.py        # (以後 Alembic 用)
├── session.py          # (以後 Session 管理)
└── checker.py          # 資料完整性、版本、健康檢查
database.py:提供 db(SQLAlchemy 實例)。
init_db.py:負責整個初始化流程，只協調其他模組。
inspector.py:檢查資料表是否存在、欄位是否一致。
creator.py:負責 create_all()、drop_all() 等建立或重建操作。
seeder.py:建立預設管理員、角色、系統設定等初始資料。
checker.py:放一些獨立的檢查工具，例如資料完整性、版本檢查等。
'''