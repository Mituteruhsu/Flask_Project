# routes/invoice_bp.py
import os
import sqlite3
from flask_login import login_required
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify

from core.database import db
from database.models.invoice import InvoiceRecord
from services.image_service import ImageService
from services.qr_service import QRService
from services.ocr_service import OCRService
from services.invoice_service import InvoiceService

invoice_bp = Blueprint("invoice", __name__, url_prefix="/invoice")

# 使用項目目錄下的 uploads 資料夾（解決 Windows /tmp 路徑問題）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 確保資料夾存在
DB_PATH = os.path.join(PROJECT_DIR, 'invoices.db')

# 路由 1：負責「圖片上傳與辨識」，不負責存入資料庫
@invoice_bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@invoice_bp.route('/scan', methods=['POST'])
@login_required
def scan():
    if request.method == 'POST':
        img_file = request.files.get('file')
        if not img_file or img_file.filename == '':
            return jsonify({
            "success": False,
            "message": "未選擇圖片"
        }), 400

        try:
            result = InvoiceService.recognize(img_file)
            return jsonify(result)

        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400
        
        except Exception as e:
            print(f"❌ 發票辨識失敗: {e}")
            return jsonify({
                "success": False,
                "message": "發票辨識失敗，請稍後再試"
            }), 500

# 路由 2（新增）：前端確認無誤後，按下確認儲存，發送 POST 請求到這裡
@invoice_bp.route('/api/save_invoice', methods=['POST'])
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

@invoice_bp.route('/base', methods=['GET'])
def base_view():
    return render_template('base.html')

@invoice_bp.route('/upload', methods=['GET'])
def upload_view():
    return render_template('upload.html')

@invoice_bp.route('/upload', methods=['POST'])
def upload_file():
    if not request.file:
        flash('檔案上傳失敗！', 'danger')  # 直接傳 danger，前端不用再做 if/else 判斷
        return redirect(url_for('upload_view'))

    flash('發票辨識成功！', 'success')  # 直接傳 success
    return redirect(url_for('upload_view'))

# 新增一個 API，讓前端隨時可以查閱歷史發票紀錄
@invoice_bp.route('/history', methods=['GET'])
def get_history():
    """ 讀取資料庫，並依時間由新到舊回傳前 50 筆發票紀錄 """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 讓讀出來的資料可以用欄位名稱選取
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
