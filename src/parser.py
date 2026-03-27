# html parser

import re
from bs4 import BeautifulSoup

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

    def extract_race_ids(self, html_content: str) -> list:
        """
        開催トップページのHTMLからその日のレースID一覧を抽出する
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        race_ids = []

        # 1. aタグのhref属性をすべてチェック
        # 地方(nar)と中央(race)両方のURLパターンに対応する正規表現
        # 例: /race/result.html?race_id=202654032801 や /race/shutuba.html?race_id=...
        pattern = re.compile(r'race_id=(\d+)')

        links = soup.find_all('a', href=pattern)

        for link in links:
            href = link.get('href')
            match = pattern.search(href)
            if match:
                race_id = match.group(1)
                race_ids.append(race_id)

        # 2. 重複を除去し、昇順に並べ替えて返す
        return sorted(list(set(race_ids)))
