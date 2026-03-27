# html parser

import re
from bs4 import BeautifulSoup

class DataParser:
    def __init__(self):
        self._any = None
        
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

    def parse_race_page(self, html, race_id):
        """
        ページから必要な情報を取得する
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # 3. レース名の確認
            # nar.netkeibaの場合、RaceName などのクラスが使われることが多い
            race_name_tag = soup.find('div', class_='RaceName')
            if race_name_tag:
                print(f"【レース名】: {race_name_tag.get_text(strip=True)}")

            # 4. 結果テーブルの構造確認
            # 全着順が入っているテーブルを探す（IDやクラス名は時期により変動あり）
            result_table = soup.find('table', id='All_Result_Table') or soup.find('table', class_='ResultTable01')
        
            if result_table:
                print("\n【テーブル構造の確認】")
                # ヘッダー（項目名）の取得
                headers = [th.get_text(strip=True) for th in result_table.find_all('th')]
                print(f"項目一覧: {headers}")

                # データのサンプル（上位3件）を表示
                rows = result_table.find_all('tr')[1:4] # 0番目はヘッダーなので1番目から
                for i, row in enumerate(rows, 1):
                    cols = [td.get_text(strip=True) for td in row.find_all('td')]
                    print(f"{i}位データ例: {cols}")
            else:
                print("\n※ 結果テーブルが見つかりませんでした。クラス名が変更されている可能性があります。")
            return None, None

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return None, None
