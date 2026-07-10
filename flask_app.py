import os
import cv2
import sqlite3
import numpy as np
from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from rapidocr import RapidOCR
from qr_service import QRService
from ocr_service import OCRService
from db_service import DB_Service


# ===========================
#       Flask App
# ===========================
app = Flask(__name__)
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
DB_Service(DB_PATH)
# ===== ↑↑↑↑↑ Database ↑↑↑↑↑ =====

# =======================================
#       Image 預處理與辨識演算法
# =======================================
def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None: return None
    h, w = img.shape
    if w > 1000:
        img = cv2.resize(img, (1000, int(h * 1000 / w)), interpolation=cv2.INTER_AREA)
    _, binary_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    output_path = os.path.join(UPLOAD_FOLDER, 'preprocessed.png')
    cv2.imwrite(output_path, binary_img)
    return output_path
# ===== ↑↑↑↑↑ Image 預處理與辨識演算法 ↑↑↑↑↑ =====

# ===========================================
#             前端路由 與 API 串接
# ===========================================
@app.route('/', methods=['GET', 'POST'])
def upload_invoice():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({"error": "未選擇圖片"})
        
        try:
            img = cv2.imdecode(np.fromfile(file, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                print(f"❌ 圖片讀取失敗！")
                exit()
            print(f"✅ 圖片讀取成功！尺寸為: {img.shape[1]}x{img.shape[0]}\n")
        except Exception as e:
            print(f"❌ 讀取圖片時發生異常: {e}")
            exit()
        
        # 1. 嘗試 QR Code 辨識
        final_data = QRService.parse_taiwan_qrcode(img)
        
        # 2. 若失敗，啟動 AI-OCR 辨識
        if not final_data:
            processed_path = preprocess_image(img)
            # 使用單例模式取得 RapidOCR 引擎，避免每次辨識都重新初始化
            ocr_engine = OCRService.get_engine()
            if processed_path:
                ocr_result, _ = ocr_engine(processed_path)
                final_data = OCRService.advanced_invoice_corrector(ocr_result)
            else:
                return jsonify({"error": "圖片損壞"})

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
