# services/ai_parser_service.py
import re

class AIParserService:
    """
    AI / Parser Service

    責任：
    1. QR / OCR 統一格式
    2. 文件大分類
    3. 發票欄位解析
    4. 商品/消費細分類
    """

    # ======================================================
    # 第一層：文件分類
    # ======================================================

    @classmethod
    def classify_document(cls, data):
        """
        第一層分類。

        QR 已符合台灣電子發票格式：
            invoice

        OCR：
            依文字判斷 invoice / receipt / unknown
        """

        if not data:
            return "unknown"

        method = data.get("辨識方法")

        if method == "QR Code":
            return "invoice"

        text = data.get("text", "")

        if cls._is_invoice_text(text):
            return "invoice"

        if cls._is_receipt_text(text):
            return "receipt"

        return "unknown"

    @staticmethod
    def _is_invoice_text(text):
        patterns = [
            r"[A-Z]{2}[- ]?\d{8}",
            r"發票",
            r"統一發票",
            r"隨機碼",
        ]

        return any(re.search(p, text, re.I) for p in patterns)

    @staticmethod
    def _is_receipt_text(text):
        patterns = [
            r"收據",
            r"receipt",
            r"小計",
            r"合計",
        ]

        return any(re.search(p, text, re.I) for p in patterns)

    # ======================================================
    # 第二層：統一資料解析
    # ======================================================

    @classmethod
    def parse(cls, data):
        """
        QR / OCR 統一入口。
        """

        if not data:
            return {
                "文件類型": "unknown",
                "分類": "OTHER",
                "細分類": "UNKNOWN",
                "辨識方法": "NONE",
            }

        document_type = cls.classify_document(data)

        # QR 已經由 QRService 按台灣規則解析完畢
        if data.get("辨識方法") == "QR Code":
            result = dict(data)

        else:
            result = cls._parse_ocr(data)

        result["文件類型"] = document_type

        # ==================================================
        # 第三層：細分類
        # ==================================================
        result.update(
            cls.classify_detail(result)
        )

        return result

    # ======================================================
    # OCR → 統一發票資料
    # ======================================================

    @classmethod
    def _parse_ocr(cls, data):
        text = data.get("text", "")

        invoice_number = cls._parse_invoice_number(text)
        total_amount = cls._parse_amount(text)

        return {
            "發票號碼": invoice_number,
            "開立日期": cls._parse_date(text),
            "推算總金額": total_amount,
            "OCR文字": text,
            "辨識方法": "AI-OCR",
        }

    @staticmethod
    def _parse_invoice_number(text):
        match = re.search(
            r"([A-Z]{2})[- ]?(\d{8})",
            text.upper()
        )

        if not match:
            return "未偵測到"

        return f"{match.group(1)}-{match.group(2)}"

    @staticmethod
    def _parse_date(text):
        patterns = [
            r"(?:民國)?(\d{2,3})[./年-](\d{1,2})[./月-](\d{1,2})",
            r"(\d{3})(\d{2})(\d{2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return "".join(match.groups())

        return "未偵測到"

    @staticmethod
    def _parse_amount(text):
        numbers = re.findall(
            r"\d+(?:\.\d+)?",
            text.replace(",", "")
        )

        values = [
            float(value)
            for value in numbers
            if float(value) > 0
        ]

        if not values:
            return "未偵測到"

        return str(int(max(values)))

    # ======================================================
    # 消費分類
    # ======================================================

    @classmethod
    def classify_detail(cls, data):
        """
        第二階段細分類。

        QRService 不做這件事情。
        """

        text = " ".join([
            str(data.get("品項明細", "")),
            str(data.get("OCR文字", "")),
        ]).lower()

        category = cls._classify_category(text)

        return {
            "分類": category,
            "細分類": cls._classify_subcategory(text, category),
        }

    @staticmethod
    def _classify_category(text):

        rules = {
            "FOOD": [
                "食品", "餐", "便當", "飲料",
                "咖啡", "麵", "飯", "水果",
                "food", "restaurant",
            ],
            "CLOTHING": [
                "衣", "褲", "鞋", "服飾",
                "clothing", "shoes",
            ],
            "MEDICAL": [
                "藥", "醫院", "診所", "醫療",
                "medical", "pharmacy",
            ],
            "HOUSING": [
                "房租", "租金", "水費", "電費",
                "瓦斯", "housing",
            ],
            "HOUSEHOLD_GOODS": [
                "日用品", "清潔", "衛生紙",
                "家具", "家用品",
            ],
            "TRANSPORT": [
                "加油", "停車", "捷運", "高鐵",
                "火車", "計程車", "transport",
            ],
            "EDUCATION": [
                "學費", "書籍", "教材", "教育",
                "education",
            ],
            "ENTERTAINMENT": [
                "電影", "遊戲", "娛樂", "ktv",
                "entertainment",
            ],
            "FINANCE": [
                "銀行", "保險", "利息", "金融",
                "finance",
            ],
        }

        for category, keywords in rules.items():
            if any(keyword.lower() in text for keyword in keywords):
                return category

        return "OTHER"

    @staticmethod
    def _classify_subcategory(text, category):

        subcategories = {
            "FOOD": {
                "咖啡": "COFFEE",
                "飲料": "DRINK",
                "便當": "MEAL",
                "餐": "RESTAURANT",
            },
            "TRANSPORT": {
                "加油": "FUEL",
                "停車": "PARKING",
                "捷運": "METRO",
                "高鐵": "HSR",
            },
            "MEDICAL": {
                "藥": "MEDICINE",
                "醫院": "HOSPITAL",
                "診所": "CLINIC",
            },
        }

        for keyword, subcategory in subcategories.get(
            category,
            {}
        ).items():

            if keyword.lower() in text:
                return subcategory

        return "OTHER"