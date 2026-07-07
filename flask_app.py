import os
import cv2
import re
from dataclasses import dataclass
import sqlite3
import numpy as np
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from rapidocr import RapidOCR
from pyzbar.pyzbar import decode

app = Flask(__name__)
# 使用項目目錄下的 uploads 資料夾（解決 Windows /tmp 路徑問題）
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # 確保資料夾存在
DB_PATH = os.path.join(PROJECT_DIR, 'invoices.db')

# 初始化超輕量 OCR 引擎
# 1. 自動取得目前程式所在的路徑，並指定本地端模型路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DET_MODEL = os.path.join(BASE_DIR, 'models', 'ch_PP-OCRv4_det_infer.onnx')
REC_MODEL = os.path.join(BASE_DIR, 'models', 'ch_PP-OCRv4_rec_infer.onnx')
print("--- 正在初始化 RapidOCR 引擎 ---")
print(f"定位模型路徑: {DET_MODEL}")
print(f"辨識模型路徑: {REC_MODEL}")
# 2. 強制載入本地端模型，避免任何網路下載行為
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
#       image 的預處理與辨識演算法
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

def parse_taiwan_qrcode(uploaded_image):
    # print(f"test the parse_taiwan_qrcode \n{uploaded_image}")
    # 使用 pyzbar 進行解碼
    barcodes = decode(uploaded_image)

    # 3. 讀取解碼結果
    for barcode in barcodes:
        # 條碼的內容 (型態為 bytes，需以 utf-8 解碼成字串)
        barcode_data = barcode.data.decode("utf-8")
        # 條碼的類型 (例如: 'QRCODE', 'CODE128')
        barcode_type = barcode.type
        
        print(f"型態: {barcode_type}, 內容: {barcode_data}")

    raw_qrs = []

    def decode_bytes(data: bytes) -> str:
        # 若 pyzbar 回傳的是已解碼字串，嘗試以 latin1 還原原始 bytes 再解碼
        if isinstance(data, str):
            try:
                return decode_bytes(data.encode("latin1"))
            except Exception:
                return data.strip()
        # 嘗試多種常見編碼，避免出現亂碼
        for enc in ("utf-8", "utf-8-sig", "big5hkscs", "big5", "cp950", "gb18030", "shift_jis", "latin1"):
            try:
                text = data.decode(enc).strip()
                if text:
                    return text
            except Exception:
                continue
        return data.decode("utf-8", errors="replace").strip()
    
    for obj in barcodes:
        try:
            data = decode_bytes(obj.data)
            # 過濾太短的資料
            if len(data) >= 8:
                raw_qrs.append(data)
        except Exception:
            continue
    print(f"services/qr_service.py QRService.decode() - decoded {len(raw_qrs)} QR codes")
    print(f"decoded QR codes: {raw_qrs}")
    
    @dataclass
    class QRCodeInfo:
        recieve: str                        # 1. 發票字軌號碼 (10)：記錄發票完整10碼字軌號碼。
        recieve_date: str                   # 2. 發票開立日期 (7)：記錄發票3碼民國年份2碼月份2碼日期共7碼。
        recieve_randam: str                 # 3. 隨機碼 (4)：記錄發票4碼隨機碼。
        recieve_sale: str                   # 4. 銷售額 (8)：記錄發票未稅總金額總計8碼，將金額轉換以十六進位方式記載。若買受人為非營業人且銷售系統無法順利將稅項分離計算，則以00000000記載，不足8碼左補0。
        recieve_total_sale: str             # 5. 總計額 (8)：記錄發票含稅總金額總計8碼，將金額轉換以十六進位方式記載，不足8碼左補0。
        recieve_buyer_invoice_num: str      # 6. 買方統一編號 (8)：記錄發票買受人統一編號，若買受人為一般消費者則以00000000記載。
        recieve_seller_invoice_num: str     # 7. 賣方統一編號 (8)：記錄發票賣方統一編號。
        recieve_AESencode: str              # 8. 加密驗證資訊 (24)：將發票字軌號碼10碼及隨機碼4碼以字串方式合併後使用AES 加密並採用 Base64 編碼轉換，AES所採用之金鑰產生方式請參考第叁、肆章及「加解密API使用說明書」。
    # ==============================================================================================================================================================================================
    # 以上欄位總計77碼。下述資訊為接續以上資訊繼續延伸記錄，且每個欄位前皆以間隔符號“:” (冒號)區隔各記載事項，若左方二維條碼不敷記載，則繼續記載於右方二維條碼。    
    # ==============================================================================================================================================================================================
        after77: str                        # 這裡是總欄位後的檔案
        recieve_free_usage: str             # 9. 營業人自行使用區 (10碼)：提供營業人自行放置所需資訊，若不使用則以10個“*”符號呈現。
        recieve_Item: str                   # 10.二維條碼記載完整品目筆數：記錄左右兩個二維條碼記載消費品目筆數，以十進位方式記載。
        recieve_totle_Item: str             # 11.該張發票交易品目總筆數：記錄該張發票記載消費品目總筆數，以十進位方式記載。
    # ==============================================================================================================================================================================================
        codetype: str                       # 12.中文編碼參數 (1碼)：定義後續資訊的編碼規格，若以：
                                            # (1) Big5編碼，則此值為0
                                            # (2) UTF-8編碼，則此值為1
                                            # (3) Base64編碼，則此值為2
    # ==============================================================================================================================================================================================
        items: str                          # 13.品名：商品名稱，請避免使用間隔符號“:”(冒號)於品名。
        item_quantity: str                  # 14.數量：商品數量，以十進位方式記載。
        items_price: str                    # 15.單價：商品單價，以十進位方式記載。
        
    def recode(x):      # 判別 0 , 1 , 2 是否為 Big5, UTF-8, Base64
        print("-----From barcode.data.decode('utf-8')----- \n", x)
        y= list(filter(None, re.search("[0-9]{1}:[0-9]{1}:[0-9]{1}:", x, flags=0).group(0).split(':'))) # 正則表達找出與關鍵類似的字元
        y= int(y[2])
        if y == 0:
            try:
                print('-----big5 decoded!!-----')
                x=x.encode('shift-jis').decode('big5')
                print(x)
                return x
            except:
                print('not decodeable')
            finally:
                return x
        elif y == 1:
            print('-----utf-8 decoded!!-----')
            return x
        elif y == 2:
            print('undefinde decode: base64') 

    def reInfo(x):
        import re
        x=recode(x) # 判別0,1,2 是否為utf-8, base64, big5
        recieve = x[:10]
        recieve_date = x[10:17]
        recieve_randam = x[17:21]
        recieve_sale_Hex = x[21:29]
        recieve_sale = str(int(recieve_sale_Hex, 16))
        recieve_total_sale_Hex = x[29:37]
        recieve_total_sale = str(int(recieve_total_sale_Hex, 16))
        recieve_buyer_invoice_num = x[37:45]
        if recieve_buyer_invoice_num == "00000000":
            recieve_buyer_invoice_num = "一般消費者"
        recieve_seller_invoice_num = x[45:53]
        recieve_AESencode = x[53:77]
        after77 = x[77:]
        y = after77.split(':')
        z = [i for i in y if i != ""]
        recieve_free_usage = z[0]
        recieve_Item = z[1]
        recieve_totle_Item = z[2]
        codetype = z[3]
        if codetype == '0': codetype = '0:Big5'
        elif codetype == '1': codetype = '1:UTF-8'
        elif codetype =='2': codetype = '2:Base64'

        # print("發票字軌(10位)    : " + self.recieve)
        # print("發票開立日期 (7位): " + self.recieve_date)
        # print("隨機碼 (4位)      : " + self.recieve_randam)
        # print("銷售額 (8位)      : " + self.recieve_sale + " 元")
        # print("總計額 (8位)      : " + self.recieve_total_sale + " 元")
        # print("買方統一編號 (8位): " + self.recieve_buyer_invoice_num)
        # print("賣方統一編號 (8位): " + self.recieve_seller_invoice_num)
        # print("加密驗證資訊(24位): " + self.recieve_AESencode)
        # print("營業人使用區(10位): " + self.recieve_free_usage)
        # print("品目筆數          : " + self.recieve_Item)
        # print("品目總筆數        : " + self.recieve_totle_Item)
        # =======span 鎖定品目比數後方資料彙整=======
        x = (x[(re.search("[0-9]{1}:[0-9]{1}:[0-9]{1}:", x, flags=0).span()[1]):]).split(":") # 正則表達找出與關鍵類似的字元
        # print(x)
        # =======split 將資料變成list一一拆解=======
        # =======將list依照[1, 3, 5]的資料連接=======
        items=' '.join(x[0:len(x):3])
        item_quantity=' '.join(x[1:len(x):3])
        items_price=' '.join(x[2:len(x):3])
        # print(items, item_quantity, items_price)
        return QRCodeInfo(
            recieve,
            recieve_date,
            recieve_randam,
            recieve_sale,
            recieve_total_sale,
            recieve_buyer_invoice_num,
            recieve_seller_invoice_num,
            recieve_AESencode,
            after77,
            recieve_free_usage,
            recieve_Item,
            recieve_totle_Item,
            codetype,
            items,
            item_quantity,
            items_price
            )

    info=reInfo(raw_qrs[0])
    if info:
        invoice_num = info.recieve                
        return {"發票號碼": invoice_num, "推算總金額": "NT$ 來自條碼", "辨識方法": "QR Code"}
    return None

def advanced_invoice_corrector(ocr_results):
    if not ocr_results: return {"發票號碼": "未偵測到", "推算總金額": "未偵測到", "辨識方法": "AI-OCR"}
    full_text = "".join([t[1].upper().replace('O', '0').replace('I', '1') for t in ocr_results])
    num_match = re.search(r'([A-Z]{2})[- ]?(\d{8})', full_text)
    invoice_number = f"{num_match.group(1)}-{num_match.group(2)}" if num_match else "未偵測到"
    
    # 簡單模擬金額抓取
    all_numbers = [int(s) for s in re.findall(r'\d+', full_text) if 1 <= len(s) <= 5]
    total_amount = f"NT$ {max(all_numbers)}" if all_numbers else "未偵測到"
    
    return {"發票號碼": invoice_number, "推算總金額": total_amount, "辨識方法": "AI-OCR"}
# ===== ↑↑↑↑↑ image 的預處理與辨識演算法 ↑↑↑↑↑ =====

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
        final_data = parse_taiwan_qrcode(img)
        
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
