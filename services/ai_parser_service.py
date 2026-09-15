# services/ai_parser.py
import re
import base64
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

# ------------------------------------------------------------------------
    @staticmethod
    def recode(data):
        """
        判斷 QR Code 的編碼方式，並進行相應的解碼
        0: Big5, 1: UTF-8, 2: Base64
        """
        print("-----From barcode.data.decode('utf-8')----- \n", data)
        y = list(filter(None, re.search("[0-9]{1}:[0-9]{1}:[0-9]{1}:", data, flags=0).group(0).split(':'))) # 正則表達找出與關鍵類似的字元
        y = int(y[2])
        if y == 0:
            try:
                print('-----big5 decoded!!-----')
                data=data.encode('shift-jis').decode('big5')
                print(data)
                return data
            except Exception:
                return data
        elif y == 1:
            print('-----utf-8 decoded!!-----')
            return data
        elif y == 2:            
            try:
                print('undefinde decode: base64')
                decoded_bytes = base64.b64decode(data)
                return decoded_bytes.decode('utf-8')
            except Exception:
                return data
        else:
            return data


    # 將 QR Code 的資料解析成 QRCodeInfo 物件，並轉換成前端可用的字典格式
    def reInfo(main_qr):
        x=self.recode(main_qr) # 判別0,1,2 是否為utf-8, base64, big5
        recieve = x[:10]
        recieve_date = x[10:17]
        recieve_randam = x[17:21]
        recieve_sale_Hex = x[21:29]
        recieve_sale = str(int(recieve_sale_Hex, 16))
        recieve_total_sale_Hex = x[29:37]
        recieve_total_sale = str(int(recieve_total_sale_Hex, 16))
        recieve_buyer_invoice_num = x[37:45]
        if recieve_buyer_invoice_num == "00000000":
            recieve_buyer_invoice_num = "一般消費者"
        recieve_seller_invoice_num = x[45:53]
        recieve_AESencode = x[53:77]
        # 第 77碼之後的資料，依照冒號分隔，並將空字串過濾掉
        after77 = x[77:]
        z = [i for i in after77.split(':') if i != ""]
        recieve_free_usage = z[0]
        recieve_Item = z[1]
        recieve_totle_Item = z[2]
        codetype = z[3]
        if codetype == '0': codetype = 'Big5'
        elif codetype == '1': codetype = 'UTF-8'
        elif codetype =='2': codetype = 'Base64'

        # print("發票字軌(10位)    : " + self.recieve)
        # print("發票開立日期 (7位): " + self.recieve_date)
        # print("隨機碼 (4位)      : " + self.recieve_randam)
        # print("銷售額 (8位)      : " + self.recieve_sale + " 元")
        # print("總計額 (8位)      : " + self.recieve_total_sale + " 元")
        # print("買方統一編號 (8位): " + self.recieve_buyer_invoice_num)
        # print("賣方統一編號 (8位): " + self.recieve_seller_invoice_num)
        # print("加密驗證資訊(24位): " + self.recieve_AESencode)
        # print("營業人使用區(10位): " + self.recieve_free_usage)
        # print("品目筆數          : " + self.recieve_Item)
        # print("品目總筆數        : " + self.recieve_totle_Item)
        # =======span 鎖定品目比數後方資料彙整=======
        x = (x[(re.search("[0-9]{1}:[0-9]{1}:[0-9]{1}:", x, flags=0).span()[1]):]).split(":") # 正則表達找出與關鍵類似的字元
        # print(x)
        # =======split 將資料變成list一一拆解=======
        # =======將list依照[1, 3, 5]的資料連接=======
        items=' '.join(x[0:len(x):3])
        item_quantity=' '.join(x[1:len(x):3])
        items_price=' '.join(x[2:len(x):3])
        # print(items, item_quantity, items_price)
        return QRCodeInfo(
            recieve,
            recieve_date,
            recieve_randam,
            recieve_sale,
            recieve_total_sale,
            recieve_buyer_invoice_num,
            recieve_seller_invoice_num,
            recieve_AESencode,
            after77,
            recieve_free_usage,
            recieve_Item,
            recieve_totle_Item,
            codetype,
            items,
            item_quantity,
            items_price
            )

     # 過濾出符合電子發票格式的 QR Code
    def find_main_qr(raw_qrs):
        """
        從多個 QR Code 中找出電子發票主資料 QR

        判斷條件：
        - 長度 >= 77
        - 包含電子發票格式
        """
        for qr in raw_qrs:
            if len(qr) >= 77 and re.match(r'^[A-Z]{2}\d{8}', qr):
                return qr.rstrip()  # 去除可能的換行符號
        print("❌ 未偵測到符合電子發票格式的 QR Code")
        return None

        # 避免 find_main_qr() 回傳 None 時，直接導致 reInfo() 報錯 
        main_qr = find_main_qr(raw_qrs)
        if main_qr is None:
            return None
        
        info=reInfo(main_qr)
        if info:
            # 將 QRCodeInfo 物件的屬性，轉換成「前端直接可以拿來跑迴圈」的中文欄位字典
            return {"發票號碼": info.recieve,
                    "開立日期": info.recieve_date,
                    "隨機碼": info.recieve_randam,
                    "銷售額": info.recieve_sale,
                    "推算總金額": info.recieve_total_sale,
                    "買方統編": info.recieve_buyer_invoice_num,
                    "賣方統編": info.recieve_seller_invoice_num,
                    "AES加密": info.recieve_AESencode,
                    "77個字元後的資料": info.after77,
                    "營業人使用區": info.recieve_free_usage,
                    "品項筆數": info.recieve_Item,
                    "品項總筆數": info.recieve_totle_Item,
                    "編碼類型": info.codetype,
                    "品項明細": info.items,
                    "品項數量": info.item_quantity,
                    "品項單價": info.items_price,
                    "辨識方法": "QR Code",
                    }
        return None
# -------------------------------------------------------------------------------
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