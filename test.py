import os
import cv2
import numpy as np
from rapidocr import RapidOCR

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
    engine = RapidOCR(
        params={"Det.model_path":DET_MODEL,
                "Rec.model_path":REC_MODEL,
                }
                )
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
# return_word_box=True 非必要，True 時會
result = engine(img, return_word_box=True)

# engine(img) 回傳值為 RapidOCROutput 這裡 = result，可透過 result.xxxx 直接存取。
# result 中預設內容包含
# img, img.shape, img.dtype
# boxes, boxes.dtype
# txts
# scores
# word_results
# elapse_list
# elapse
# viser
# 常使用包含以下欄位：
# result.img (np.ndarray)：傳入的原始影像。
# result.boxes (np.ndarray)：影像中每行座標框，shape 為 (N, 4, 2)。N 表示有多少文字行。
# result.txts (Tuple[str])：與 boxes 文字框對應辨識出的文字內容。長度與 RapidOCROutput.boxes 長度一致。
# result.scores (Tuple[float])：每行辨識文字結果的信心水準（置信度）。長度與 RapidOCROutput.boxes 長度一致。
# result.word_results (Tuple[Any])：此部分結果僅在 return_word_box=True 時才會有值。
# result.elapse_list (List[float])：文字偵測、文字行方向分類與文字辨識等三個部分各自的推論耗時，單位為秒。
# result.elapse (float)：三個部分整體的耗時，單位為秒。
print(f"⏱️ 文字偵測、文字行方向分類與文字辨識三個部分各別的推論耗時: \n文字偵測   :{result.elapse_list[0]:.4f}秒\n文字行方向分類:{result.elapse_list[1]:.4f}秒\n文字辨識   :{result.elapse_list[2]:.4f}秒")
print(f"⏱️ 辨識整體耗時: {result.elapse:.4f} 秒\n")

# # 6. 輸出結果到終端機
# if result:
#     print("📊 [辨識結果清單]")
#     print("-" * 50)
#     # 用 enumerate() 來建立排序，將 result 中的列表放入 index 從 1 開始
#     for index, (box, text, score) in enumerate(zip(result.boxes, result.txts, result.scores), 1):
#         # box: 文字外框的四個座標
#         # text: 辨識出的文字內容
#         # score: 信心值 (0.0 ~ 1.0)
#         print(f"第 {index} 行:")
#         print(f"  內容: {text}")
#         print(f"  信心值: {score:.2f}")
#         print(f"  座標位置: {box}")
#         print("-" * 50)
# else:
#     print("⚠️ 辨識完成，但沒有在圖片中找到任何文字！")

# # 讀取單字級別結果 (因為 return_word_box=True)
# if result.word_results is not None:
#     print("🔍 [單字/單詞級別精準定位 - 逐字完美切分版]")
#     print("-" * 50)
    
#     char_count = 1  # 建立一個全局的文字計數器
    
#     # 1. 外層迴圈：遍歷每一「行」的文字元組
#     for line_index, line_words in enumerate(result.word_results, 1):
        
#         # 2. 內層迴圈：遍歷這一行裡面的「每一個字」
#         for word_info in line_words:
            
#             # 3. 完美解包：此時的 word_info 保證是標準的 ('卡', 0.9665, [[...]])
#             # 我們使用強制轉成 list 或是直接解包皆可，這裡直接解包
#             word_text, word_score, word_box = word_info
            
#             # 4. 漂亮格式化輸出
#             print(f"單詞 {char_count} (第 {line_index} 行): 【{word_text}】")
#             print(f"  - 信心度: {word_score:.4f}")
#             # 安全檢查 word_box 是否支援 tolist()，將其轉為乾淨的標準 list
#             print(f"  - 獨立外框座標: {word_box.tolist() if hasattr(word_box, 'tolist') else word_box}")
#             print("-" * 50)
            
#             char_count += 1  # 序號往下加
# else:
#     print("未開啟 return_word_box 或未偵測到文字")

# 內建 Markdown 排列
print(result.to_markdown())
print(type(result.to_markdown()))
