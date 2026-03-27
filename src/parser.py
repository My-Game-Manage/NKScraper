# html parser

import re
from bs4 import BeautifulSoup

from src.constants.schema import RaceCol
from src.utils.helpers import get_jyo_name

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
            
            # レース基本情報
            race_name_tag = soup.select_one(".RaceName")
            race_name = race_name_tag.get_text(strip=True) if race_name_tag else ""
        
            race_data_tag = soup.select_one(".RaceData01")
            race_data = race_data_tag.get_text(strip=True) if race_data_tag else ""
        
            # 距離と種別の抽出 (例: ダ1600m)
            dist_match = re.search(r'(ダ|芝|障)(\d+)m', race_data)
            condition = dist_match.group(1) if dist_match else ""
            distance = dist_match.group(2) if dist_match else ""
        
            course_name = get_jyo_name(race_id)
            race_num = int(race_id[-2:])

            race_info_list = []
            horse_ids = []
        
            # 出馬表の行をループ
            rows = soup.select("tr.HorseList")
            for row in rows:
                # 【重要】馬名リンクがない行は馬のデータではないのでスキップ
                h_tag = row.select_one(".HorseName a")
                if not h_tag:
                    continue
                r_info = self._get_entryhorse_info_from_row(row, race_name, condition, distance, course_name, race_num)
                if r_info:
                    race_info_list.append(r_info)
                    horse_ids.append(r_info['馬ID'])
            
                if h_id: horse_ids.append(h_id)

            return race_info_list, horse_ids
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return None, None

    def _get_entryhorse_info_from_row(self, row: list, race_name, condition, distance, course_name, race_num) -> dict:
        """
        テーブルから出走馬の情報を取得し、辞書にして返す
        """
        # 枠番・馬番（部分一致セレクタを使用）
        waku_tag = row.select_one("td[class*='Waku']")
        waku = waku_tag.get_text(strip=True) if waku_tag else ""
            
        umaban_tag = row.select_one("td[class*='Umaban']")
        umaban = umaban_tag.get_text(strip=True) if umaban_tag else ""
            
        # 馬名・ID
        h_tag = row.select_one(".HorseName a")
        h_name = h_tag.get_text(strip=True) if h_tag else ""
        h_id = re.search(r'horse/(\d+)', h_tag['href']).group(1) if h_tag and 'href' in h_tag.attrs else ""

        # 性齢：class="Age" を使用／中央はclass="Barei"を使用
        age_td = row.select_one(".Age")
        if not age_td:
            age_td = row.select_one(".Barei")
        sex, age = self._split_sex_age(age_td.get_text(strip=True)) if age_td else (None, None)
            
        # 斤量：td:nth-of-type(6) を使用
        kinryo_td = row.select_one("td:nth-of-type(6)")
        kinryo = kinryo_td.get_text(strip=True) if kinryo_td else ""
            
        # 騎手・厩舎
        jockey = row.select_one(".Jockey a").get_text(strip=True) if row.select_one(".Jockey a") else ""
        trainer = row.select_one(".Trainer").get_text(strip=True) if row.select_one(".Trainer") else ""
            
        # 馬体重の分離
        weight_tag = row.select_one(".Weight") # 独立したWeightクラス（馬体重用）
        weight_raw = weight_tag.get_text(strip=True) if weight_tag else ""
        weight, weight_diff = self._split_weight(weight_raw)

        return {
            RaceCol.COURSE: course_name,
            RaceCol.RACE_NUMBER: race_num,
            RaceCol.RACE_NAME: race_name,
            RaceCol.SURFACE: condition,
            RaceCol.DISTANCE: distance,
            RaceCol.BRACKET_NUM: waku,
            RaceCol.HORSE_NUM: umaban,
            RaceCol.HORSE_NAME: h_name,
            RaceCol.FATHER: 'Unknown',
            RaceCol.MOTHER: 'Unknown',
            RaceCol.SEX: sex,
            RaceCol.AGE: age,
            RaceCol.WEIGHT_CARRIED: kinryo,
            RaceCol.JOCKEY: jockey,
            RaceCol.STABLE: trainer,
            RaceCol.HORSE_WEIGHT: weight,
            RaceCol.WEIGHT_DIFF: weight_diff,
            RaceCol.HORSE_ID: h_id,
        }
        
    def _split_weight(self, weight_str):
        """'518(0)' -> 518, 0 / '496(-1)' -> 496, -1"""
        if not weight_str or weight_str == "計不" or weight_str == "**":
            return None, None
        # 正規表現で 数字 と ( ) 内の数字を抽出
        match = re.search(r'(\d+)\(([+-]?\d+)\)', weight_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        # 括弧がない場合（初出走など）
        match_only_weight = re.search(r'(\d+)', weight_str)
        if match_only_weight:
            return int(match_only_weight.group(1)), None
        return None, None

    def _split_sex_age(self, sei_rei):
        """'牡4' -> '牡', 4 / '牝3' -> '牝', 3"""
        if not sei_rei:
            return None, None
        # 先頭1文字を性別、残りを年齢として抽出
        sex = sei_rei[0]
        try:
            age = int(re.search(r'\d+', sei_rei).group())
            return sex, age
        except:
            return sex, None
