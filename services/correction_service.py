# services/correction_service.py
from flashtext import KeywordProcessor
from database.services.CRUD.services import correction_dictionary_service

class CorrectionService:
    @classmethod
    def initialize_keyword_processor(cls):
        """
        初始化 KeywordProcessor，將資料庫中的錯字與正確字對應加入
        """
        clean_processor = KeywordProcessor(case_sensitive=False)
        clean_processor.non_word_boundaries = set() # 清空預設邊界，強迫所有文字與符號都獨立計算

        rows = correction_dictionary_service.filter_by(is_active=True, is_deleted=False)

        for row in rows:
                clean_processor.add_keyword(row.alias, row.canonical_name)   # (原始錯字, 標準字)

        return clean_processor

    @classmethod
    def correct_text(cls, text):
        """
        使用 KeywordProcessor 進行文字修正
        """
        keyword_processor = cls.initialize_keyword_processor()
        corrected_text = keyword_processor.replace_keywords(text)
        print("=== 錯字自動修正完成 ===")
        # for i, line in enumerate(corrected_text.strip().split("\n")):
        #     print(f"第 {i+1:02d} 行: {line}")
        return corrected_text