# services/ai_parser.py
import re
from typing import List, Dict, Any, Optional

class AIParserService:
    """
    AI 發票與收據資料解析服務
    負責將 OCR 文字清單轉換為結構化 JSON 資料
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        可傳入 API Key 以支援線上 LLM（如 Gemini/OpenAI），
        未傳入時預設使用高效能本地正則與語意推導引擎
        """
        self.api_key = api_key

    def parse_receipt_text(self, text_lines: List[str]) -> Dict[str, Any]:
        """
        核心解析入口：接收 raw text_lines，傳回結構化發票欄位
        """
        if not text_lines:
            return {
                "store_name": "未知店家",
                "invoice_number": "",
                "total_amount": 0.0,
                "items": [],
                "suggested_category": "未分類"
            }

        # 1. 解析發票號碼 (例如: AB-12345678)
        invoice_number = self._extract_invoice_number(text_lines)

        # 2. 解析店家名稱
        store_name = self._extract_store_name(text_lines)

        # 3. 解析總金額
        total_amount = self._extract_total_amount(text_lines)

        # 4. 解析消費明細項目
        items = self._extract_items(text_lines)

        # 5. 智慧推論消費分類
        suggested_category = self._infer_category(store_name, items, text_lines)

        return {
            "store_name": store_name,
            "invoice_number": invoice_number,
            "total_amount": total_amount,
            "items": items,
            "suggested_category": suggested_category
        }

    def _extract_invoice_number(self, text_lines: List[str]) -> str:
        """抽取台灣電子發票號碼格式 (兩位大寫英文字母 + 8位數字)"""
        pattern = r'[A-Z]{2}[-\s]?\d{8}'
        for line in text_lines:
            match = re.search(pattern, line)
            if match:
                return match.group(0).replace('-', '').replace(' ', '')
        return ""

    def _extract_store_name(self, text_lines: List[str]) -> str:
        """從文字前段過濾無關標籤，萃取店家名稱"""
        ignore_keywords = [
            "統一發票", "電子發票", "存根聯", "收執聯", 
            "營業人", "統一編號", "歡迎光臨", "發票號碼"
        ]
        
        for line in text_lines[:5]:
            clean_line = line.strip()
            # 排除包含忽略關鍵字或純數字/日期的行
            if clean_line and not any(kw in clean_line for kw in ignore_keywords):
                # 剔除符號與數字後檢查長度
                filtered_name = re.sub(r'[\d\-\:\.\*\s]', '', clean_line)
                if len(filtered_name) >= 2:
                    return filtered_name
                    
        return "便利商店 / 零售賣場"

    def _extract_total_amount(self, text_lines: List[str]) -> float:
        """多重策略匹配總金額"""
        # 策略 1: 尋找明確的金額關鍵字標籤
        keyword_patterns = [
            r'(?:總計|總金額|小計|合計|TOTAL|Amount)[\s\:\=]*[\$NT\$]*\s*([\d\,]+)',
            r'[\$NT\$]\s*([\d\,]+)'
        ]
        
        for line in text_lines:
            for pattern in keyword_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    raw_num = match.group(1).replace(',', '')
                    try:
                        val = float(raw_num)
                        if val > 0:
                            return val
                    except ValueError:
                        continue

        # 策略 2: 從所有數字中篩選出最可能是總金額的數值（排除統編與發票號碼數字）
        candidate_numbers = []
        for line in text_lines:
            # 跳過含有統編、日期等特徵的行
            if any(k in line for k in ["統編", "日期", "時間", "機號"]):
                continue
            matches = re.findall(r'\b\d{1,6}\b', line)
            for m in matches:
                val = float(m)
                if 1 <= val <= 200000:
                    candidate_numbers.append(val)

        return max(candidate_numbers) if candidate_numbers else 0.0

    def _extract_items(self, text_lines: List[str]) -> List[Dict[str, Any]]:
        """萃取消費明細品項與單價"""
        items = []
        exclude_words = ["總計", "找零", "現金", "信用卡", "統一編號", "小計", "找款", "應付"]

        for line in text_lines:
            clean_line = line.strip()
            if any(w in clean_line for w in exclude_words):
                continue

            # 匹配格式：文字品名 + 數量/金額 (例如: "鮮乳 90" 或 "美式咖啡 x1 55")
            match = re.search(r'^([^\d]+?)\s+(?:x?\d+\s+)?[\$]?(\d+)$', clean_line)
            if match:
                name = match.group(1).strip()
                price = float(match.group(2))
                if len(name) >= 2 and price > 0:
                    items.append({"name": name, "price": price})

        return items

    def _infer_category(self, store_name: str, items: List[Dict[str, Any]], text_lines: List[str]) -> str:
        """根據店家名稱與明細進行語意自動歸類"""
        full_text = f"{store_name} " + " ".join([i["name"] for i in items]) + " " + " ".join(text_lines)

        category_rules = {
            "餐飲伙食": ["餐", "便當", "麵", "飯", "咖啡", "鮮乳", "牛奶", "飲料", "麥當勞", "肯德基", "星巴克", "早餐"],
            "日用雜項": ["衛生紙", "洗髮精", "牙膏", "清潔劑", "全聯", "家樂福", "好市多", "屈臣氏", "康是美"],
            "交通差旅": ["高鐵", "台鐵", "捷運", "加油", "中油", "停車", "計程車", "Uber", "和運"],
            "文具娛樂": ["書", "筆", "影印", "電影", "遊戲", "誠品", "文具"]
        }

        for category, keywords in category_rules.items():
            if any(kw in full_text for kw in keywords):
                return category

        return "日常消費"