# html parser

from src.constants.master_data import JYO_NAME_MAP

class DataParser:
    def __init__(self):
        self._any = None
        
    def get_jyo_name(self, kaisai_id: str) -> str:
        """10桁または12桁のIDから会場名を特定"""
        if not kaisai_id or len(kaisai_id) < 6:
            return "不明"
            
        code = kaisai_id[4:6]
        # 定数から取得。なければ "不明" を返す
        return JYO_NAME_MAP.get(code, "不明")
