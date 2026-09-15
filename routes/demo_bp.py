# routes/demo_bp.py
from flask import Blueprint, request, jsonify, session
from services.invoice_service import InvoiceService


demo_bp = Blueprint("demo", __name__, url_prefix="/demo")

# ======================================================
# Demo 限制
# ======================================================

MAX_DEMO_SCANS = 3
MAX_FILE_SIZE = 10 * 1024 * 1024


def _demo_limit():
    """限制同一個 Session 的 Demo 次數。"""

    count = session.get("demo_scan_count", 0)

    if count >= MAX_DEMO_SCANS:
        return False

    session["demo_scan_count"] = count + 1
    return True


def _validate_file(file):
    """基本 Demo 檔案驗證。"""

    if not file or not file.filename:
        return False, "未選擇圖片"

    content_length = request.content_length or 0

    if content_length > MAX_FILE_SIZE:
        return False, "圖片不可超過 10MB"

    allowed = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    filename = file.filename.lower()

    if not any(filename.endswith(ext) for ext in allowed):
        return False, "只允許 JPG、PNG、WEBP"

    return True, None


# ======================================================
# Demo Page
# ======================================================

@demo_bp.route("/", methods=["GET"])
def index():
    return jsonify({
        "demo": True,
        "remaining": max(
            0,
            MAX_DEMO_SCANS - session.get("demo_scan_count", 0)
        )
    })


# ======================================================
# Demo Scan
# ======================================================

@demo_bp.route("/scan", methods=["POST"])
def scan():

    if not _demo_limit():
        return jsonify({
            "success": False,
            "message": "Demo 次數已用完，請登入後繼續使用"
        }), 429

    file = request.files.get("file")

    valid, message = _validate_file(file)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    try:
        result = InvoiceService.recognize(file)

        # Demo 絕對不回傳資料庫資訊
        result.pop("id", None)
        result.pop("user_id", None)
        result.pop("workspace_id", None)

        result["demo"] = True
        result["儲存"] = False

        return jsonify(result)

    except Exception as exc:
        print(f"Demo Error: {exc}")

        return jsonify({
            "success": False,
            "message": "Demo 辨識失敗"
        }), 500