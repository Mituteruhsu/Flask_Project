import os
import sqlite3
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from flask_wtf import CSRFProtect
from services.image_service import ImageService
from services.qr_service import QRService
from services.ocr_service import OCRService
from services.db_service import DBService, InvoiceRecord, db

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

# 核心：初始化 db 並與 app 綁定，防呆資料庫初始化，自動檢查並建立所有資料表
DBService.init_db(app)
# ===== ↑↑↑↑↑ Database ↑↑↑↑↑ =====

# ===========================================
#             前端路由 與 API 串接
# ===========================================
# 路由 1：負責「圖片上傳與辨識」，不負責存入資料庫
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
        
        return jsonify(final_data)
        
    return render_template('index.html')

# 路由 2（新增）：前端確認無誤後，按下確認儲存，發送 POST 請求到這裡
@app.route('/api/save_invoice', methods=['POST'])
def save_invoice():
    """ 接收前端確認後的資料，並正式寫入 SQLAlchemy 資料庫 """
    try:
        # 從前端的 AJAX 請求中取得 JSON 資料
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "無效的發票資料"}), 400

        # 改用 SQLAlchemy ORM 語法將資料寫入
        new_record = InvoiceRecord(
            invoice_num=data.get("發票號碼"),
            invoice_date=data.get("開立日期"),
            random_code=data.get("隨機碼"),
            sales_amount=data.get("銷售額"),
            total_amount=data.get("推算總金額"),
            buyer_invoice_num=data.get("買方統編"),
            seller_invoice_num=data.get("賣方統編"),
            aes_encode=data.get("AES加密"),
            after77_data=data.get("77個字元後的資料"),
            free_usage=data.get("營業人使用區"),
            item_count=data.get("品項筆數"),
            total_item_count=data.get("品項總筆數"),
            code_type=data.get("編碼類型"),
            items_detail=data.get("品項明細"),
            item_quantity=data.get("品項數量"),
            items_price=data.get("品項單價"),
            method=data.get("辨識方法", "QR Code"),
            user_id=None  # 初期尚未串接登入系統，先設為 None
        )
        
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"success": True, "message": "發票紀錄儲存成功！"})
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 資料庫儲存失敗: {e}")
        return jsonify({"success": False, "message": f"資料庫儲存失敗: {e}"}), 500

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
