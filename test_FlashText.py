from flashtext import KeywordProcessor

# 1. 準備您剛才提供的 RapidOCR 原始混亂字串
ocr_result_str = """
COSTCO
VVHOLESAVLE
新社店#5011
新北市新莊區242
建國--路138號
SALE
金星鲁員 89311066301
迷你葡萄乾糍饼
152362   1x    198    198
羲美厚豆奶
132566    1x     149    149  T
美國球鞋甘蓝
716578    1x     265    265
萬品素蛋饼皮
47077    1x     109    109 T
美國特嫩肩牛排
92223    1x   1,420  1,420
產销腹歷青花菜
66165    1x    145   145
简蒿菜
54449     1x      79      79
埃及蒜頭900G
297772    1x    229    229
有機青江菜500G
93855     1x      65      65
116624有機A菜500G1x     69      69
産銷履歷彩色甜椒
77026     1x     249    249
KS抽取式衛生纸
109999   1x    369    369 T
商品數小計=12
(T=含税）
總金额 (T)     3.346
聯名卡            0
红利抵用      3.346
找霉            0

0170672026 13:58 5011 18 180 1017
卡號：2447
<GUI>XA62478634
卡献具
"""

# ==========================================
# 任務一：使用 FlashText 進行「單據類型特徵識別」
# ==========================================
type_processor = KeywordProcessor()

# 設定特徵字典：當看到哪些字，就歸類為哪種單據特徵
type_processor.add_keyword("1x", "ITEMIZED_INVOICE")
type_processor.add_keyword("商品數小計", "ITEMIZED_INVOICE")
type_processor.add_keyword("交易授權碼", "CARD_SLIP")
type_processor.add_keyword("簽名", "CARD_SLIP")

# 一微秒提取特徵
detected_types = type_processor.extract_keywords(ocr_result_str)
print("=== 1. 單據特徵識別結果 ===")
print(f"偵測到的單據特徵標籤: {set(detected_types)}")
if "ITEMIZED_INVOICE" in detected_types:
    print("-> 路由分流決策：此單據包含商品細項，準備啟動『發票細項解析器』\n")


# ==========================================
# 任務二：使用 FlashText 進行「OCR 錯字自動修正」
# ==========================================
clean_processor = KeywordProcessor()

# 設定校正字典：add_keyword(標準答案, 錯字或變體)
# 這部分非常適合直接從您的資料庫 (Database) 動態讀取載入！
clean_processor.add_keyword("Wholesale", "VVHOLESAVLE")
clean_processor.add_keyword("新莊店", "新社店")
clean_processor.add_keyword("找零", "找霉")
clean_processor.add_keyword("產銷履歷", "産銷履歷")
clean_processor.add_keyword("產銷履歷", "產销腹歷")

# 一微秒完成整篇文字的局部錯字替換
cleaned_str = clean_processor.replace_keywords(ocr_result_str)

print("=== 2. 錯字自動修正結果 ===")
# 為了方便對比，我們印出前 15 行清洗後的結果
for i, line in enumerate(cleaned_str.strip().split("\n")[:15]):
    print(f"第 {i+1:02d} 行: {line}")
