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
        process_image = ImageService.preprocess_image(image_file)  # 先進行圖片預處理
        # 1. 嘗試 QR Code 辨識
        final_data = QRService.decode_qrcode(process_image)

        # 2. 若失敗，啟動 AI-OCR 辨識
        if not final_data:
            print("❌ QR Code 辨識失敗，啟動 AI-OCR 辨識")
            final_data = OCRService.ocr_process(process_image)

        # 3. 將辨識結果用 ai_parser_service 進行結構化解析
        if final_data:            
            ai_parser_service = AIParserService()
            structured_data = ai_parser_service.parse_receipt_text(final_data)
            return structured_data