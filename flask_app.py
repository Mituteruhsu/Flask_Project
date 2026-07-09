import os
import cv2
import re
import sqlite3
import numpy as np
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from rapidocr import RapidOCR
from pyzbar.pyzbar import decode
from qr_service import QRService


# ===========================
#       Flask App
# ===========================
app = Flask(__name__)
# 使用項目目錄下的 uploads 資料夾（解決 Windows /tmp 路徑問題）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 確保資料夾存在
DB_PATH = os.path.join(PROJECT_DIR, 'invoices.db')

# ===============================
#      初始化 RapidOCR Engine
# ===============================
# 1. 取得目前程式所在的路徑，並指定本地端模型路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DET_MODEL = os.path.join(BASE_DIR, 'models', 'ch_PP-OCRv4_det_infer.onnx')
REC_MODEL = os.path.join(BASE_DIR, 'models', 'ch_PP-OCRv4_rec_infer.onnx')
print("--- 正在初始化 RapidOCR 引擎 ---")
print(f"定位模型路徑: {DET_MODEL}")
print(f"辨識模型路徑: {REC_MODEL}")

# 2. 強制載入本地端模型，避免網路下載
try:
    engine = RapidOCR(
        params={"Det.model_path":DET_MODEL,
                "Rec.model_path":REC_MODEL,
                }
                )
    print("✅ RapidOCR 引擎初始化成功！\n")
except Exception as e:
    print(f"❌ 引擎初始化失敗，錯誤原因: {e}")
    exit()

# ========================
#       Database
# ========================
def init_db():
    """ 初始化 SQLite 資料庫：如果檔案不存在會自動建立，並建立繁體中文欄位表 """
    conn = sqlite3.connect(DB_PATH)
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

# 程式啟動時，立即初始化或檢查資料庫
init_db()

def save_to_database(invoice_num, total_amount, method):
    """ 將辨識成功的發票資料，安全地寫入 SQLite 資料庫 """
    try:
        conn = sqlite3.connect(DB_PATH)
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



def advanced_invoice_corrector(ocr_results):
    if not ocr_results: return {"發票號碼": "未偵測到", "推算總金額": "未偵測到", "辨識方法": "AI-OCR"}
    full_text = "".join([t[1].upper().replace('O', '0').replace('I', '1') for t in ocr_results])
    num_match = re.search(r'([A-Z]{2})[- ]?(\d{8})', full_text)
    invoice_number = f"{num_match.group(1)}-{num_match.group(2)}" if num_match else "未偵測到"
    
    # 簡單模擬金額抓取
    all_numbers = [int(s) for s in re.findall(r'\d+', full_text) if 1 <= len(s) <= 5]
    total_amount = f"NT$ {max(all_numbers)}" if all_numbers else "未偵測到"
    
    return {"發票號碼": invoice_number, "推算總金額": total_amount, "辨識方法": "AI-OCR"}
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
        
        # 4. 支援中文路徑的安全讀取機制
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
            if processed_path:
                ocr_result, _ = engine(processed_path)
                final_data = advanced_invoice_corrector(ocr_result)
            else:
                return jsonify({"error": "圖片損壞"})

        # 【核心新增】將辨識出的結果，即時寫入 SQLite 資料庫中記錄
        save_to_database(
            invoice_num=final_data["發票號碼"],
            total_amount=final_data["推算總金額"],
            method=final_data["辨識方法"]
        )
        
        return jsonify(final_data)
        
    return render_template('index.html')

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
    app.run(debug=True)
