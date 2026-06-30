import os
import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

# 1. 自動取得目前程式所在的路徑，並指定本地端模型路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DET_MODEL = os.path.join(BASE_DIR, 'models', 'ch_PP-OCRv4_det_infer.onnx')
REC_MODEL = os.path.join(BASE_DIR, 'models', 'ch_PP-OCRv4_rec_infer.onnx')

# DET_MODEL & REC_MODEL：組裝出本地端模型檔案的正確位置。
# det 代表 Detection（文字定位模型）：負責在圖片中找出「哪裡有文字」，並把位置圈出來。
# rec 代表 Recognition（文字辨識模型）：負責把圈出來的圖片區域，真正「看懂並轉換成文字字串」。
# 這裡使用的是百度開源、非常強大的 PP-OCRv4 模型的 ONNX 格式。
print("--- 正在初始化 RapidOCR 引擎 ---")
print(f"定位模型路徑: {DET_MODEL}")
print(f"辨識模型路徑: {REC_MODEL}")

# 2. 強制載入本地端模型，避免任何網路下載行為
try:
    engine = RapidOCR(det_model_path=DET_MODEL, rec_model_path=REC_MODEL)
    print("✅ RapidOCR 引擎初始化成功！\n")
except Exception as e:
    print(f"❌ 引擎初始化失敗，錯誤原因: {e}")
    exit()

# 3. 指定您的測試發票圖片檔名（請確保圖片與此程式放在同一個資料夾）
IMAGE_NAME = 'recive_20260106_Costco_ocr01.jpg' 
IMAGE_NAME2 = 'recive_20260106_Costco_ocr02.jpg'
IMAGE_PATH = os.path.join(BASE_DIR, IMAGE_NAME2)

print(f"--- 正在讀取圖片: {IMAGE_NAME} ---")

# 4. 支援中文路徑的安全讀取機制
try:
    img = cv2.imdecode(np.fromfile(IMAGE_PATH, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        print(f"❌ 圖片讀取失敗！請確認 {IMAGE_NAME} 是否確實存在於該目錄下。")
        exit()
    print(f"✅ 圖片讀取成功！尺寸為: {img.shape[1]}x{img.shape[0]}\n")
except Exception as e:
    print(f"❌ 讀取圖片時發生異常: {e}")
    exit()

# 5. 執行文字辨識
print("--- 開始進行 AI 文字辨識 ---")
result, elapse = engine(img)

print(f"⏱️ 辨識耗時: {elapse} 秒\n")

# 6. 輸出結果到終端機
if result:
    print("📊 [辨識結果清單]")
    print("-" * 50)
    for index, (box, text, score) in enumerate(result, 1):
        # box: 文字外框的四個座標
        # text: 辨識出的文字內容
        # score: 信心值 (0.0 ~ 1.0)
        print(f"第 {index} 行:")
        print(f"  內容: {text}")
        print(f"  信心值: {score:.2f}")
        print(f"  座標位置: {box}")
        print("-" * 50)
else:
    print("⚠️ 辨識完成，但沒有在圖片中找到任何文字！")
