# ocr_service.py
import os
import re
from flask import jsonify
from rapidocr import RapidOCR

class OCRService:
    # ===============================
    #      初始化 RapidOCR Engine
    # ===============================
    # 取得目前程式所在的路徑，並指定本地端模型路徑
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DET_MODEL = os.path.join(BASE_DIR, 'models_OCR_onnx', 'ch_PP-OCRv4_det_infer.onnx')
    REC_MODEL = os.path.join(BASE_DIR, 'models_OCR_onnx', 'ch_PP-OCRv4_rec_infer.onnx')
    print("=== 初始化 RapidOCR Engine - ocr_service.py ===")
    
    _engine = None  # 用來儲存單一引擎實例

    @classmethod
    def get_engine(cls):
        """ 確保 RapidOCR 引擎只初始化一次的單例模式 """
        if cls._engine is None:
            print("get_engine()\n--- 正在初始化 RapidOCR 引擎 ---")
            print(f"定位模型路徑: {cls.DET_MODEL}")
            print(f"辨識模型路徑: {cls.REC_MODEL}")
            # 載入本地端模型，避免網路下載
            try:
                cls._engine = RapidOCR(
                    params={"Det.model_path":cls.DET_MODEL,
                            "Rec.model_path":cls.REC_MODEL,
                            }
                )
                print("✅ RapidOCR 引擎初始化成功！\n")
            except Exception as e:
                print(f"❌ 引擎初始化失敗，錯誤原因: {e}")
                raise e
        return cls._engine
    
    @staticmethod  # 👈 定義它是純工具函式
    def ocr_process(processed_image):
        """ 使用 RapidOCR 進行文字辨識 """
        print("ocr_process() - 正在進行文字辨識...")
        # 使用單例模式取得 RapidOCR 引擎，避免每次辨識都重新初始化
        ocr_engine = OCRService.get_engine()
        ocr_result = ocr_engine(processed_image)
        if ocr_result:
            print(f"✅ AI-OCR 辨識結果:\n {ocr_result.to_markdown()}")
        else:
            return jsonify({"error": "圖片損壞"})

    @classmethod
    def advanced_invoice_corrector(cls, ocr_results):
        """ 轉換並推算發票資料的演算法 """
        if not ocr_results: 
            return {"發票號碼": "未偵測到", "推算總金額": "未偵測到", "辨識方法": "AI-OCR"}
        
        full_text = "".join([t[1].upper().replace('O', '0').replace('I', '1') for t in ocr_results])
        num_match = re.search(r'([A-Z]{2})[- ]?(\d{8})', full_text)
        invoice_number = f"{num_match.group(1)}-{num_match.group(2)}" if num_match else "未偵測到"
        
        # 簡單模擬金額抓取
        all_numbers = [int(s) for s in re.findall(r'\d+', full_text) if 1 <= len(s) <= 5]
        total_amount = f"NT$ {max(all_numbers)}" if all_numbers else "未偵測到"
        
        return {"發票號碼": invoice_number, "推算總金額": total_amount, "辨識方法": "AI-OCR"}