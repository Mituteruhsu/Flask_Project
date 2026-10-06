from flashtext import KeywordProcessor
from run import app
from database.services.CRUD.services import correction_dictionary_service

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
# 任務二：使用 FlashText 進行「OCR 錯字自動修正」
# ==========================================
# 【關鍵關鍵！】初始化時加上其餘的字元集，讓它與繁簡中文、標點符號全面相容
clean_processor = KeywordProcessor()
clean_processor.non_word_boundaries = set() # 清空預設邊界，強迫所有文字與符號都獨立計算

# 查 DB 需要 Flask app context
with app.app_context():
    rows = correction_dictionary_service.filter_by(is_active=True, is_deleted=False)

    # 在 context 內就把需要的欄位取出來，避免 session 結束後存取 ORM 物件
    for row in rows:
        clean_processor.add_keyword(row.alias, row.canonical_name)   # (原始錯字, 標準字)

print(f"✅ 已從資料庫載入 {len(rows)} 筆修正字典")
if not rows:
    print("⚠️ 字典是空的，請確認 seed_correction_dictionaries() 是否已執行")

# 完成整篇文字的局部錯字替換
cleaned_str = clean_processor.replace_keywords(ocr_result_str)

print("=== 錯字自動修正結果 ===")
for i, line in enumerate(cleaned_str.strip().split("\n")):
    print(f"第 {i+1:02d} 行: {line}")
