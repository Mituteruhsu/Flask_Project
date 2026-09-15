# services/invoice_service.py
import os
import tempfile
from services.image_service import ImageService
from services.qr_service import QRService
from services.ocr_service import OCRService
from services.ai_parser_service import AIParserService

class InvoiceService:
    @classmethod
    def recognize(cls, image_file):
        """
        負責整合 QR Code 辨識與 AI-OCR 辨識的流程
        1. 先進行圖片預處理
        2. 嘗試 QR Code 辨識
        3. 若失敗，啟動 AI-OCR 辨識
        """
        if not image_file:
            return {"error": "未提供圖片檔案"}

        # 先進行圖片預處理
        process_image = ImageService.preprocess_image(image_file)

        # 1. 嘗試 QR Code 辨識
        qr_data = QRService.decode_qrcode(process_image)
        if qr_data:
            return AIParserService.parse(qr_data)

        # 2. 若失敗，啟動 AI-OCR 辨識
        if not qr_data:
            print("❌ QR Code 辨識失敗，啟動 AI-OCR 辨識")
            ocr_data = OCRService.ocr_process(process_image)
            if not ocr_data:
                return {
                "成功": False,
                "文件類型": "unknown",
                "分類": "OTHER",
                "細分類": "UNKNOWN",
                "訊息": "無法辨識圖片",
                }
            result = AIParserService.parse(ocr_data)
            result["成功"] = True
            return result

    @staticmethod
    def _preprocess(file_storage):
        """
        將上傳的檔案轉換為臨時檔案，並返回其路徑
        """
        suffix = os.path.splitext(file_storage.filename or ".jpg")[1]
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=suffix, delete=False
            ) as temp:
                file_storage.save(temp)
                temp_path = temp.name
            return ImageService.preprocess_image(temp_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)