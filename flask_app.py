import os
import sqlite3
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from flask_wtf import CSRFProtect
from image_service import ImageService
from qr_service import QRService
from ocr_service import OCRService
from db_service import DB_Service


# ===========================
#       Flask App
# ===========================
app = Flask(__name__)

# 隨機產生一個 SECRET_KEY，確保 CSRF 保護的安全性
app.config['SECRET_KEY'] = os.urandom(24)
csrf = CSRFProtect(app)
# print(f"Flask App 啟動中，使用的 SECRET_KEY 為: {app.config['SECRET_KEY']}")

# 設定 Jsonify 不要自動排序 key，保持原本的順序
app.json.sort_keys = False  
# 使用項目目錄下的 uploads 資料夾（解決 Windows /tmp 路徑問題）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 確保資料夾存在
DB_PATH = os.path.join(PROJECT_DIR, 'invoices.db')
# ===== ↑↑↑↑↑ Flask App ↑↑↑↑↑ =====

# ========================
#       Database
# ========================
# 程式啟動時，立即初始化或檢查資料庫
# 配置 Flask-SQLAlchemy 連線路徑
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# ===== ↑↑↑↑↑ Database ↑↑↑↑↑ =====

# ===========================================
#             前端路由 與 API 串接
# ===========================================
@app.route('/', methods=['GET', 'POST'])
def upload_invoice():
    if request.method == 'POST':
        img_file = request.files.get('file')
        if not img_file or img_file.filename == '':
            return jsonify({"error": "未選擇圖片"})
        
        # 先將圖片預處理，嘗試 QR Code 辨識
        processed_image = ImageService.preprocess_image(img_file)
        
        # 1. 嘗試 QR Code 辨識
        final_data = QRService.parse_taiwan_qrcode(processed_image)
        
        # 2. 若失敗，啟動 AI-OCR 辨識
        if not final_data:
            print("❌ QR Code 辨識失敗，啟動 AI-OCR 辨識")
            final_data = OCRService.ocr_process(processed_image)

        # 將辨識出的結果，即時寫入 SQLite 資料庫中記錄
        DB_Service(DB_PATH).save_to_database(
            invoice_num=final_data["發票號碼"],
            total_amount=final_data["推算總金額"],
            method=final_data["辨識方法"]
        )
        
        return jsonify(final_data)
        
    return render_template('index.html')

@app.route('/base', methods=['GET'])
def base_view():            
    return render_template('base.html')

@app.route('/upload', methods=['GET'])
def upload_view():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if not request.file:
        flash('檔案上傳失敗！', 'danger') # 直接傳 danger，前端不用再做 if/else 判斷
        return redirect(url_for('upload_view'))
    
    flash('發票辨識成功！', 'success') # 直接傳 success
    return redirect(url_for('upload_view'))

# 新增一個 API，讓前端隨時可以查閱歷史發票紀錄
@app.route('/history', methods=['GET'])
def get_history():
    """ 讀取資料庫，並依時間由新到舊回傳前 50 筆發票紀錄 """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # 讓讀出來的資料可以用欄位名稱選取
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM invoice_records ORDER BY created_at DESC LIMIT 50')
    rows = cursor.fetchall()
    conn.close()
    
    history_list = []
    for row in rows:
        history_list.append({
            "序號": row["id"],
            "發票號碼": row["invoice_num"],
            "總金額": row["total_amount"],
            "辨識管道": row["method"],
            "記錄時間": row["created_at"]
        })
    return jsonify(history_list)
# ===== ↑↑↑↑↑ 前端路由 與 API 串接 ↑↑↑↑↑ =====

if __name__ == '__main__':
    # app.run(debug=True)
    # host='0.0.0.0' 代表監聽所有網路介面
    # port=8000 可以自訂埠號（預設是 5000）
    app.run(host='0.0.0.0', port=8000, debug=True)
