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

SELECTOR_TAG = {
    RaceCol.RACE_DATA: ".RaceData01",
    RaceCol.RACE_NAME: ".RaceName",
    RaceCol.BRACKET_NUM: "td[class*='Waku']",
    RaceCol.HORSE_NUM: "td[class*='Umaban']",
    RaceCol.WEIGHT_CARRIED: "td:nth-of-type(6)",
    RaceCol.JOCKEY: ".Jockey a",
    RaceCol.STABLE: ".Trainer",
    RaceCol.HORSE_NAME: ".HorseName a",
    RaceCol.AGE: ".Age",
    RaceCol.HORSE_WEIGHT: ".Weight",
}

SELECTOR_TAG_NAR = {
    RaceCol.AGE: ".Barei",
}

SELECTOR_TAG_HORSE = {
    RaceCol.HORSE_NAME: ".horse_title h1, .db_head_name h1",
    RaceCol.FATHER: ".b_ml",
    RaceCol.MOTHER: ".b_fml",
}

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
        出馬表ページから必要な情報を取得する
        """
        self.logger.info(f"race-id {race_id} into parse_race_page: start processing ...")
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            condition, distance = self._get_cond_and_dist(soup)
            
            race_info_list = []
            horse_ids = []

            # レース情報
            race_data = {
                RaceCol.RACE_NAME: self._get_race_name(soup),     # レース名
                RaceCol.SURFACE: condition,                       # 馬場
                RaceCol.DISTANCE: distance,                       # 距離
                RaceCol.COURSE: get_jyo_name(race_id),            # 開催場所
                RaceCol.RACE_NUMBER: self._get_race_num(race_id), # レース番号
            }
            self.logger.debug(f"race_data: {race_data}")
        
            # 出馬表の行をループ
            rows = soup.select("tr.HorseList")
            for row in rows:
                # 【重要】馬名リンクがない行は馬のデータではないのでスキップ
                h_tag = row.select_one(SELECTOR_TAG[RaceCol.HORSE_NAME])
                if not h_tag:
                    continue
                row_info = self._get_entryhorse_info_from_row(row)
                self.logger.debug(f"row_info: {row_info}")
                if row_info:
                    race_info_list.append(race_data | row_info)
                    horse_ids.append(row_info[RaceCol.HORSE_ID])

            return race_info_list, horse_ids
        except Exception as e:
            self.logger.warning(f"エラーが発生しました: {e}")
            return None, None

    def parse_horse_history(self, html: str, horse_id: str):
        """
        馬の過去レースデータを取得する
        """
        self.logger.info(f"horse_id: {horse_id} の過去履歴の取得開始...")
        try:
            soup = BeautifulSoup(html, 'html.parser')
        
            # 父母馬名の取得
            sire_names = self._get_sire_names(horse_id, soup)
        
            # tableからDataFrameを作成
            dfs = pd.read_html(StringIO(html))
            res_df = pd.DataFrame()
            for df in dfs:
                if '日付' in df.columns:
                    res_df = df.copy()
                    break
            
            if res_df.empty:
                return res_df, sire_names

            # 1. カラム名のクリーニング（スペース除去）＆ 全要素のクリーニング
            res_df = self.normalizer.normalize_horse_history_columns(res_df)

            # 3. 馬体重の分割
            if '馬体重' in res_df.columns:
                res_df[['体重', '体重増減']] = res_df['馬体重'].apply(
                    lambda x: pd.Series(self._split_weight(x))
                )

            # 4. 距離の数値化と種別の分離
            if '距離' in res_df.columns:
                res_df['種別'] = res_df['距離'].str.extract(r'([ダ芝障])')
                res_df['距離'] = res_df['距離'].str.extract(r'(\d+)').astype(float)

            # 5. 基本情報の付与
            res_df['馬ID'] = horse_id
            res_df['馬名'] = self._get_elm_by_selector(soup, SELECTOR_TAG_HORSE[RaceCol.HORSE_NAME])

            self.logger.debug(f"res_df: {res_df}")

            # 6. カラムの正規化（並び替えも込み）
            valid_df = self.normalizer.normalize_columns(res_df)

            return valid_df, sire_names

        except Exception as e:
            self.logger.warning(f"解析エラー (HorseID: {horse_id}): {e}")
            return pd.DataFrame(), sire_names
            
    def parse_race_result_page(self, html: str, race_id: str) -> list:
        """
        レース結果ページから情報取得
        """
        self.logger.info(f"race-id {race_id} into parse_race_result_page: start processing ...")
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # 種別、距離
            condition, distance = self._get_cond_and_dist(soup)
            # レース情報
            race_data = {
                RaceCol.RACE_NAME: self._get_race_name(soup),     # レース名
                RaceCol.SURFACE: condition,                       # 馬場
                RaceCol.DISTANCE: distance,                       # 距離
                RaceCol.COURSE: get_jyo_name(race_id),            # 開催場所
                RaceCol.RACE_NUMBER: self._get_race_num(race_id), # レース番号
            }
            self.logger.info(f"race_data: {race_data}")
            # 出馬表の行をループ
            rows = soup.select("tr.HorseList")
            for row in rows:
                # 【重要】馬名リンクがない行は馬のデータではないのでスキップ
                h_tag = row.select_one(SELECTOR_TAG[RaceCol.HORSE_NAME])
                if not h_tag:
                    continue
                result = self._get_entryhorse_result_from_row(row)
                self.logger.info(f"result: {result}")
                if result:
                    race_info_list.append(race_data | result)
            return []
        except Exception as e:
            self.logger.warning(f"エラーが発生しました: {e}")
            return None, None
        
    def _get_entryhorse_info_from_row(self, row: BeautifulSoup) -> dict:
        """
        テーブルから出走馬の情報を取得し、辞書にして返す
        """
        self.logger.debug(f"get_entryhorse_info_from_row: start processing ...")
        # 馬名・ID
        h_name, h_id = self._get_horse_name_and_horse_id(row)

        # 性齢：class="Age" を使用／中央はclass="Barei"を使用
        sex, age = self._get_horse_sex_and_age(row)
            
        # 馬体重の分離
        weight, weight_diff = self._get_horse_weight_and_diff(row)

        return {
            RaceCol.BRACKET_NUM: self._get_horse_waku(row),
            RaceCol.HORSE_NUM: self._get_horse_umaban(row),
            RaceCol.HORSE_NAME: h_name,
            RaceCol.FATHER: 'Unknown',
            RaceCol.MOTHER: 'Unknown',
            RaceCol.SEX: sex,
            RaceCol.AGE: age,
            RaceCol.WEIGHT_CARRIED: self._get_horse_kinryo(row),
            RaceCol.JOCKEY: self._get_horse_jockey(row),
            RaceCol.STABLE: self._get_horse_trainer(row),
            RaceCol.HORSE_WEIGHT: weight,
            RaceCol.WEIGHT_DIFF: weight_diff,
            RaceCol.HORSE_ID: h_id,
        }

    def _get_entryhorse_result_from_row(self, row: BeautifulSoup) -> dict:
        """
        テーブルから出走馬の結果情報を取得し、辞書にして返す
        """
        self.logger.debug(f"get_entryhorse_result_from_row: start processing ...")
        
        # 馬名・ID
        h_name, h_id = self._get_horse_name_and_horse_id(row)
        
        # 性齢：class="Age" を使用／中央はclass="Barei"を使用
        sex, age = self._get_horse_sex_and_age(row)            
        
        # 馬体重の分離
        weight, weight_diff = self._get_horse_weight_and_diff(row)
        
        return {
            RaceCol.RANK: "着順",
            RaceCol.BRACKET_NUM: self._get_horse_waku(row),
            RaceCol.HORSE_NUM: self._get_horse_umaban(row),
            RaceCol.HORSE_NAME: h_name,
            RaceCol.SEX: sex,
            RaceCol.AGE: age,
            RaceCol.WEIGHT_CARRIED: self._get_horse_kinryo(row),
            RaceCol.JOCKEY: self._get_horse_jockey(row),
            RaceCol.TIME: "タイム",
            RaceCol.RANK_DIFF: "着差",
            RaceCol.POPULAR: "人気",
            RaceCol.ODDS: "オッズ",
            RaceCol.LAST_3F: "上り",
            RaceCol.PASS: "通過順",
            RaceCol.STABLE: self._get_horse_trainer(row),
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
            
    def _get_elm_by_selector(self, soup: BeautifulSoup, selector: str) -> str:
        elm_tag = soup.select_one(selector)
        return elm_tag.get_text(strip=True) if elm_tag else ""

    def _get_race_name(self, soup: BeautifulSoup) -> str:
        return self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.RACE_NAME])

    def _get_race_num(self, race_id: str) -> str:
        return int(race_id[-2:])

    def _get_cond_and_dist(self, soup: BeautifulSoup) -> list:
        # レース基本情報
        race_data = self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.RACE_DATA])
        
        # 距離と種別の抽出 (例: ダ1600m)
        dist_match = re.search(r'(ダ|芝|障)(\d+)m', race_data)
        condition = dist_match.group(1) if dist_match else ""
        distance = dist_match.group(2) if dist_match else ""
        return condition, distance

    def _get_horse_waku(self, soup: BeautifulSoup) -> str:
        return self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.BRACKET_NUM])

    def _get_horse_umaban(self, soup: BeautifulSoup) -> str:
        return self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.HORSE_NUM])
        
    def _get_horse_kinryo(self, soup: BeautifulSoup) -> str:
        return self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.WEIGHT_CARRIED])

    def _get_horse_jockey(self, soup: BeautifulSoup) -> str:
        return self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.JOCKEY])

    def _get_horse_trainer(self, soup: BeautifulSoup) -> str:
        return self._get_elm_by_selector(soup, SELECTOR_TAG[RaceCol.STABLE])

    def _get_horse_name_and_horse_id(self, soup: BeautifulSoup) -> list:
        h_tag = soup.select_one(SELECTOR_TAG[RaceCol.HORSE_NAME])
        h_name = h_tag.get_text(strip=True) if h_tag else ""
        h_id = re.search(r'horse/(\d+)', h_tag['href']).group(1) if h_tag and 'href' in h_tag.attrs else ""
        return h_name, h_id
        
    def _get_horse_sex_and_age(self, soup: BeautifulSoup) -> list:
        age_td = soup.select_one(SELECTOR_TAG[RaceCol.AGE])
        if not age_td:
            age_td = soup.select_one(SELECTOR_TAG_NAR[RaceCol.AGE])
        return self._split_sex_age(age_td.get_text(strip=True)) if age_td else (None, None)
        
    def _get_horse_weight_and_diff(self, soup: BeautifulSoup) -> list:
        weight_tag = soup.select_one(SELECTOR_TAG[RaceCol.HORSE_WEIGHT]) # 独立したWeightクラス（馬体重用）
        weight_raw = weight_tag.get_text(strip=True) if weight_tag else ""
        return self._split_weight(weight_raw)

    def _get_sire_names(self, horse_id: str, soup: BeautifulSoup) -> dict:
        dad_name = self._get_elm_by_selector(soup, SELECTOR_TAG_HORSE[RaceCol.FATHER])
        mam_name = self._get_elm_by_selector(soup, SELECTOR_TAG_HORSE[RaceCol.MOTHER])
        return {
            RaceCol.HORSE_ID: horse_id,
            RaceCol.FATHER: dad_name if dad_name else "Unknown",
            RaceCol.MOTHER: mam_name if mam_name else "Unknown",
        }
