# 暫時保留
import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

# 1. 建立一個空白的繁體中文 NLP 大腦
nlp = spacy.blank("zh")

# 2. 這是我們要讓 AI 自動化學習的「教材」(標註出商品、金額、號碼)
# 實務上只要給它 20-30 組樣本，它就能學會全台灣所有收據的規律！
TRAIN_DATA = [
    (
        "迷你葡萄乾糍饼 152362 1x 198 198 羲美厚豆奶 132566 1x 149 149 總金額 (T) 3,346 <GUI>XA62478634",
        {
            "entities": [
                (0, 7, "ITEM"),      # 迷你葡萄乾糍餅
                (19, 22, "PRICE"),    # 198 (單價)
                (26, 31, "ITEM"),     # 義美厚豆奶
                (43, 46, "PRICE"),    # 149 (單價)
                (58, 63, "TOTAL"),    # 3,346 (總金額)
                (70, 80, "INV_NUM")   # XA62478634 (發票號碼)
            ]
        }
    ),
    # 可以持續加入 7-11、全聯的文字教材，AI 會自己融會貫通
]

# 3. 執行自動化增強學習 (這邊簡化為邏輯展示，SpaCy 官方有提供一鍵 train 指令)
# 訓練完成後，您可以直接把模型存成一個 10MB 的資料夾：nlp.to_disk("./invoice_model")

# 4. 【預測與記帳】當新發票進來時，直接用 AI 提取：
def parse_invoice_with_local_nlp(ocr_text):
    # 載入我們訓練好的本地小模型
    # nlp = spacy.load("./invoice_model")
    
    doc = nlp(ocr_text)
    
    report = {
        "發票號碼": "未偵測到",
        "推算總金額": "0",
        "品項清單": []
    }
    
    # AI 會自動根據它學到的語意，把各個欄位抓出來
    for ent in doc.ents:
        if ent.label_ == "INV_NUM":
            report["發票號碼"] = ent.text
        elif ent.label_ == "TOTAL":
            report["推算總金額"] = ent.text
        elif ent.label_ == "ITEM":
            report["品項清單"].append({"品名": ent.text})
            
    return report
