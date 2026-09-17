# services/test_parser.py
import re

class COSTCOParserService:

    @classmethod
    def parse_from_raw_ocr(cls, boxes, txts):
        """
        純本地端高效能入口：直接接收 RapidOCR 的原始 boxes 和 txts
        """
        
        # 1. 將資料重組，並計算每個框的幾何邊界
        ocr_elements = []
        for box, text in zip(boxes, txts):
            # box 格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [p[0] for p in box]
            y_coords = [p[1] for p in box]
            
            ocr_elements.append({
                "text": text.strip(),
                "x_min": min(x_coords),
                "x_max": max(x_coords),
                "y_min": min(y_coords),
                "y_max": max(y_coords),
                "y_center": sum(y_coords) / 4.0,
                "x_center": sum(x_coords) / 4.0
            })

        # 2. 找出最重要的大欄位 (發票號碼、日期、總金額)
        all_joined_text = "\n".join([el["text"] for el in ocr_elements])
        invoice_num = cls._parse_invoice_number(all_joined_text)
        invoice_date = cls._parse_date(all_joined_text)
        total_amount = cls._parse_amount(all_joined_text, ocr_elements)

        # 3. 核心：幾何空間品項黏合演算法
        items_detail = cls._geometry_bind_items(ocr_elements)

        return {
            "發票號碼": invoice_num,
            "開立日期": invoice_date,
            "推算總金額": total_amount,
            "品項明細": items_detail,
            "品項總筆數": len(items_detail),
            "辨識方法": "Pure-Local-Geometry-OCR"
        }

    @classmethod
    def _geometry_bind_items(cls, elements):
        """
        利用 2D 空間幾何位置，強行黏合「品名」與「價格行」
        """
        price_lines = []
        potential_names = []

        # 分流：區分哪些元素是「價格行」，哪些是「可能是品名的文字」
        for el in elements:
            text = el["text"]
            # 特徵：包含 1x/2x，或是尾端有連動數字加 T (如 109 109 T)
            is_price = "1x" in text or "2x" in text or re.search(r'\b\d+\b.*\b\d+\b.*T?', text)
            
            # 排除系統關鍵字與純發票號碼
            if any(k in text.upper() for k in ["COSTCO", "總金額", "TOTAL", "合計", "小計", "聯名卡", "找霉", "卡號", "<GUI>"]):
                continue

            if is_price:
                price_lines.append(el)
            else:
                # 長度大於 2 且不全是數字的視為潛在品名
                if not text.replace(" ", "").isdigit() and len(text) > 1:
                    potential_names.append(el)

        final_items = []

        # 幾何配對：幫每一個「價格行」尋找它的「正上方或左上方」品名
        for price_el in price_lines:
            best_match_name = "未知商品"
            min_distance = float('inf')

            for name_el in potential_names:
                # 條件 1：品名必須在價格行的「上方」（Y軸判定）
                # 考慮到好市多排版，品名的 Y 中心點必須小於價格行的 Y 中心點
                if name_el["y_center"] >= price_el["y_center"]:
                    continue
                
                # 條件 2：品名和價格在垂直方向不能隔太遠 (設定上限，避免跨商品錯位)
                y_distance = price_el["y_center"] - name_el["y_center"]
                if y_distance > 150: # 像素距離上限，可依圖片解析度微調
                    continue

                # 條件 3：X 軸算重疊度或水平距離
                # 好市多品名在左邊，價格在右邊。品名的左側(x_min)通常跟價格行差不多，或更靠左
                x_distance = abs(name_el["x_min"] - price_el["x_min"])

                # 綜合空間距離計算 (加權：Y軸距離越近、X軸起點越對齊越好)
                total_score = y_distance + (x_distance * 0.5)

                if total_score < min_distance:
                    min_distance = total_score
                    best_match_name = name_el["text"]

            # 解析價格行文字抓出數字
            nums = re.findall(r'[\d,]+', price_el["text"])
            price = int(nums[-1].replace(",", "")) if nums else 0
            qty = 2 if "2x" in price_el["text"] else 1

            if price < 100000: # 防禦長條碼數字
                final_items.append({
                    "品名": best_match_name,
                    "數量": qty,
                    "單價": price,
                    "小計": qty * price
                })

        # 依照發票從上到下的順序重新排序商品
        final_items.sort(key=lambda x: x.get("小計", 0), reverse=True) # 範例先用金額排，也可記錄 Y 座標來排
        return final_items

    @staticmethod
    def _parse_amount(all_text, ocr_elements):
        """ 幾何強化版金額抓取 """
        # 優先找「總金額」關鍵字方框右邊或下方的數字
        lines = all_text.replace(",", "").split("\n")
        for line in lines:
            match = re.search(r'(?:總金額|TOTAL|合計)[^\d]*(\d+)', line, re.I)
            if match:
                val = int(match.group(1))
                if 0 < val < 1000000: return str(val)
        
        # 備援：找合理的百萬內最大純數字
        nums = [int(s.replace(",", "")) for s in re.findall(r'\b\d{1,5}\b', all_text)]
        return str(max(nums)) if nums else "0"

    @staticmethod
    def _parse_invoice_number(text):
        match = re.search(r'([A-Z]{2})[- ]?(\d{8})', text.upper())
        return f"{match.group(1)}-{match.group(2)}" if match else "未偵測到"

    @staticmethod
    def _parse_date(text):
        # 尋找 8 碼或 10 碼包含 2026 的數字串
        match = re.search(r'(\d{2})[./-]?(\d{2})[./-]?(20\d{2})', text)
        if match: return f"{match.group(3)}/{match.group(1)}/{match.group(2)}"
        return "未偵測到"
