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

        if isinstance(data, str):
            if cls._is_invoice_text(data):
                return "invoice"
            if cls._is_receipt_text(data):
                return "receipt"
            return "unknown"

        method = data.get("辨識方法")

        if method == "QR Code":
            return "invoice"

        text = data.get("text", "") if isinstance(data, dict) else str(data)

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

        if isinstance(data, str):
            data = {"辨識方法": "AI-OCR", "text": data}

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
        if isinstance(data, dict):
            text = data.get("text", "")
        else:
            text = str(data)

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
            r"(\d{4})[./年-](\d{1,2})[./月-](\d{1,2})",  # 西元制 (2026/01/06)
            r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})",      # 美式西元制 (01/06/2026)
            r"(?:民國)?(\d{2,3})[./年-](\d{1,2})[./月-](\d{1,2})",  # 民國制
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                g = match.groups()
                # 如果年份在後面 (美式 01/06/2026)
                if len(g[2]) == 4:
                    return f"{g[2]}{g[0].zfill(2)}{g[1].zfill(2)}" # 統一轉為 YYYYMMDD
                # 如果年份在前面 (2026/01/06)
                elif len(g[0]) == 4:
                    return f"{g[0]}{g[1].zfill(2)}{g[2].zfill(2)}"
                # 民國制
                return "".join(g)

        return "未偵測到"

    @staticmethod
    def _parse_amount(text):
        # 移除逗號，但保留換行與空格
        clean_text = text.replace(",", "")

        # 針對好市多收據的「 總金額 (T) 3346 」或「 TOTAL 3346 」進行嚴格文字定位
        # [^\d\n]* 意思是中間可以允許空格或符號，但不允許換行到別行去抓數字
        amount_patterns = [
            r"總金額\s*\(T\)[^\d\n]*(\d+)",
            r"總金額[^\d\n]*(\d+)",
            r"合計[^\d\n]*(\d+)",
            r"TOTAL[^\d\n]*(\d+)",
            r"實付[^\d\n]*(\d+)"
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, clean_text, re.I)
            if match:
                return match.group(1)

        # 備援機制：如果真的找不到關鍵字，絕不使用 max() 瞎抓，而是尋找最後出現在下方的合理金額
        # 發票金額通常在倒數幾行
        lines = [line.strip() for line in clean_text.split("\n") if line.strip()]
        for line in reversed(lines):
            # 尋找單獨成行的數字，通常可能是總金額
            if line.isdigit() and len(line) <= 6: # 一般消費總額很少超過 6 位數
                return line

        return "未偵測到"

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
                "food", "restaurant", "蘇打餅", "牛肉", "青花菜", "茼蒿" # 新增好市多常見食物關鍵字
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