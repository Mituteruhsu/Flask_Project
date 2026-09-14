# routes/demo_bp.py
from flask import Blueprint, request, jsonify
from services.ocr_service import OCRService
from services.ai_parser import AIParserService

demo_bp = Blueprint("demo", __name__, url_prefix="/api/demo")

# 初始化服務實例
ocr_service = OCRService()
ai_parser_service = AIParserService()


@demo_bp.route("/scan", methods=["POST"])
def demo_scan_invoice():
    """
    公開沙盒體驗 API (無需登入權限)
    接收使用者上傳圖片 -> 執行 OCR -> 執行 AIParser -> 回傳結構化資料 (不儲存至 DB)
    """
    if "file" not in request.files:
        return jsonify({
            "success": False, 
            "message": "請選擇發票或收據圖片檔案"
        }), 400

    file = request.files["file"]
    image_bytes = file.read()

    if not image_bytes:
        return jsonify({
            "success": False, 
            "message": "上傳的檔案內容為空白"
        }), 400

    try:
        # 1. 執行 OCR 文字檢測與辨識 (呼叫既有 OCR 服務)
        ocr_result = ocr_service.run_ocr(image_bytes)
        raw_text_lines = ocr_result.get("text_lines", [])

        # 2. 呼叫剛實作完成的 AIParserService 進行語意結構化
        parsed_data = ai_parser_service.parse_receipt_text(raw_text_lines)

        # 3. 回傳前端 JSON 結果
        return jsonify({
            "success": True,
            "data": {
                "store_name": parsed_data["store_name"],
                "invoice_number": parsed_data["invoice_number"],
                "total_amount": parsed_data["total_amount"],
                "items": parsed_data["items"],
                "category": parsed_data["suggested_category"],
                "time_saved_seconds": 180
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"影像辨識處理失敗: {str(e)}"
        }), 500