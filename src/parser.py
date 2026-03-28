# html parser

import re
import pandas as pd
import numpy as np
from io import StringIO
from bs4 import BeautifulSoup

from src.utils.logger import setup_logger
from src.constants.schema import RaceCol
from src.utils.helpers import get_jyo_name
from src.normalizer import DataNormalizer

class DataParser:
    """
    データを適切な形で取得する
    """
    def __init__(self):
        _CLASSNAME = "DataParser"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger(_CLASSNAME)

        self.logger.info("初期化しています...")

        self.normalizer = DataNormalizer()
        
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
        self.logger.info(f"race-id {race_id} into parse_race_page: start processing ...")
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

            # 固定部分をまとめる
            fixed_data = {
                RaceCol.RACE_NAME: race_name,
                RaceCol.SURFACE: condition,
                RaceCol.DISTANCE: distance,
                RaceCol.COURSE: course_name,
                RaceCol.RACE_NUMBER: race_num,
            }
            self.logger.debug(f"fixed_data: {fixed_data}")
        
            # 出馬表の行をループ
            rows = soup.select("tr.HorseList")
            for row in rows:
                # 【重要】馬名リンクがない行は馬のデータではないのでスキップ
                h_tag = row.select_one(".HorseName a")
                if not h_tag:
                    continue
                row_info = self._get_entryhorse_info_from_row(row)
                self.logger.debug(f"row_info: {row_info}")
                if row_info:
                    race_info_list.append(fixed_data | row_info)
                    horse_ids.append(row_info[RaceCol.HORSE_ID])

            return race_info_list, horse_ids
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return None, None

    def parse_horse_history(self, html: str, horse_id: str):
        """
        馬の過去レースデータを取得する
        """
        self.logger.info(f"horse_id: {horse_id} の過去履歴の取得開始...")
        try:
            soup = BeautifulSoup(html, 'html.parser')
        
            # 馬名の取得
            name_tag = soup.select_one(".horse_title h1, .db_head_name h1")
            horse_name = name_tag.get_text(strip=True) if name_tag else "不明"

            # 父母馬名の取得
            sire_dad_name = soup.select_one(".b_ml").get_text(strip=True) if soup.select_one(".b_ml") else "Unknown"
            sire_mam_name = soup.select_one(".b_fml").get_text(strip=True) if soup.select_one(".b_fml") else "Unknown"
            sire_names = {
                RaceCol.HORSE_ID: horse_id,
                RaceCol.FATHER: sire_dad_name,
                RaceCol.MOTHER: sire_mam_name,
            }
        
            # tableからDataFrameを作成
            dfs = pd.read_html(StringIO(html))
            res_df = pd.DataFrame()
            for df in dfs:
                if '日付' in df.columns:
                    res_df = df.copy()
                    break
            
            if res_df.empty:
                return res_df, sire_names

            # 1. カラム名のクリーニング（スペース除去）
            res_df.columns = [c.replace(' ', '').replace('　', '') for c in res_df.columns]
            
            # 2. 全要素のクリーニング（Pandas 2.1.0+ 対応の map を使用）
            res_df = res_df.map(lambda x: x.strip().replace(' ', '').replace('　', '') if isinstance(x, str) else x)

            # 3. 馬体重の分割
            if '馬体重' in res_df.columns:
                res_df[['体重', '体重増減']] = res_df['馬体重'].apply(
                    lambda x: pd.Series(self._split_weight(x))
                )

            # 4. 距離の数値化と種別の分離
            if '距離' in res_df.columns:
                res_df['種別'] = res_df['距離'].str.extract(r'([ダ芝障])')
                res_df['距離'] = res_df['距離'].str.extract(r'(\d+)').astype(float)

            # タイムの秒変換
            #if 'タイム' in res_df.columns:
            #    res_df['タイム'] = res_df['タイム'].apply(self._time_to_seconds)

            # 5. 基本情報の付与
            res_df['馬ID'] = horse_id
            res_df['馬名'] = horse_name

            # 6. 【重要】カラムの並び替え
            # ユーザー指定の順序: 馬ID, 馬名, 日付, ... 種別, 距離, ...
            ordered_cols = [
                '馬ID', '馬名', '日付', '開催', '天気', 'R', 'レース名', '頭数', '枠番', '馬番',
                'オッズ', '人気', '着順', '騎手', '斤量', '種別', '距離', '馬場',
                'タイム', '着差', '通過', '上り', '体重', '体重増減', '勝ち馬(2着馬)', '賞金'
            ]
            
            # 存在するカラムのみで再構成
            final_cols = [c for c in ordered_cols if c in res_df.columns]
            res_df = res_df[final_cols]
            self.logger.debug(f"res_df: {res_df}")

            # カラムの正規化
            valid_df = self.normalizer.normalize_columns(res_df)

            return valid_df, sire_names

        except Exception as e:
            print(f"解析エラー (HorseID: {horse_id}): {e}")
            return pd.DataFrame(), sire_names

    def _get_entryhorse_info_from_row(self, row: list) -> dict:
        """
        テーブルから出走馬の情報を取得し、辞書にして返す
        """
        self.logger.debug(f"get_entryhorse_info_from_row: start processing ...")
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
