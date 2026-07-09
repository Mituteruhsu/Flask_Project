import sqlite3
from datetime import datetime

class DB_Service:
    def __init__(self, db_path):
        print(f"正在初始化資料庫服務: {db_path}")
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """ 初始化 SQLite 資料庫：如果檔案不存在會自動建立，並建立繁體中文欄位表 """
        print(f"檢查或建立資料庫表格: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS invoice_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        invoice_num TEXT NOT NULL,
                        total_amount TEXT,
                        method TEXT,
                        created_at TEXT
                        )
                        ''')
        conn.commit()
        conn.close()

    def save_to_database(self, invoice_num, total_amount, method):
        """ 將辨識成功的發票資料，安全地寫入 SQLite 資料庫 """
        print(f"正在將發票資料寫入資料庫: {self.db_path}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO invoice_records (invoice_num, total_amount, method, created_at)
                VALUES (?, ?, ?, ?)
            ''', (invoice_num, total_amount, method, current_time))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"資料庫寫入失敗: {e}")
            return False