"""
collector.py の概要
このクラスの主な責務は以下の3つです。

1. 依存クラスの集約: NetKeibaClient（通信）、DataParser（解析）、DataNormalizer（修正）を束ねる。
2. 実行フローの制御: 「ID取得 → HTML取得 → パース → 正規化 → 保存」という一連の流れを実行する。
3. 環境管理: 保存先ディレクトリの作成や、重複データのチェック（キャッシュ管理）を行う。
"""

import os
import time
from enum import Enum
from src.constants.schema import NetkeibaPageType
from src.netkeiba_client import NetKeibaClient
from src.parser import DataParser
from src.normalizer import DataNormalizer  # 先ほど提案した正規化クラス
from src.utils.date_utils import normalize_date_format, get_today_jst
from src.utils.logger import setup_logger
from src.utils.helpers import (
    get_top_page_url, get_jyo_name,
    filter_race_ids_exclude_course, filter_race_ids_by_course, filter_race_ids_by_number,
    get_race_url, get_horse_url,
    override_race_info_parents_name,
)

class DataType(Enum):
    SHUTUBA = "出馬表"
    HISTORY = "過去履歴"
    RESULT = "レース結果"

DEFAULT_BASE_DIR = 'data'


class RaceDataCollector:
    def __init__(self, headless: bool = True, base_dir: str = DEFAULT_BASE_DIR):
        """
        初期化: 必要なコンポーネントのインスタンス化とディレクトリ準備
        """
        _CLASSNAME = "Collector"
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger("Collector")

        self.logger.info("Collectorを初期化しています...")
        
        # 1. 道具（コンポーネント）の準備
        self.client = NetKeibaClient(headless=headless)
        self.parser = DataParser()
        self.normalizer = DataNormalizer() # 表記ゆれ対策用
        self.processed_horse_ids = set()
        
        # 2. パス・ディレクトリの設定
        self.base_dir = base_dir
        
        # ディレクトリがなければ作成する
        os.makedirs(self.base_dir, exist_ok=True)

        # 3. 実行状態の管理（同じ馬を何度も取得しないためのキャッシュなど）
        self.processed_horse_ids = set()

    def run(self, target_date=None, course_filter=None, race_num_filter=None, is_result: bool=False, only_race: bool=False):
        """
        メインの実行メソッド
        """
        self.logger.info("Collectorを実行開始します...")
        
        # 1. レースID一覧を取得（client）
        target_race_ids = self._get_target_race_ids(target_date, course_filter, race_num_filter)
        self.logger.info(f"target_race_ids: {len(target_race_ids)}件取得しました")

        # 2. 各レースの処理（client＆normalizer）＞ソース取得・情報取得・整形・表記修正
        race_info_list, horse_ids, horse_info_list, race_result_list = [], [], [], []
        if is_result:
            race_result_list = self._get_race_result_from_ids(target_race_ids)
            self.logger.info(f"race_result_list: {len(race_result_list)}件取得しました")
        else:
            race_info_list, horse_ids = self._get_race_infos_from_ids(target_race_ids, only_race)
            self.logger.info(f"race_info_list: {len(race_info_list)}件取得しました")
            self.logger.info(f"horse_ids: {len(horse_ids)}件取得しました")
            if horse_ids and not only_race:
                # 馬レース履歴はまとめて取得
                horse_info_list, sire_names_list = self._get_horse_infos_from_ids(horse_ids)
                self.logger.info(f"horse_info_list: {len(horse_info_list)}件取得しました")
                # 父母馬名の上書き
                race_info_list = override_race_info_parents_name(race_info_list, sire_names_list)
            
        # 3. CSVとして保存
        if race_info_list:
            self._save_to_csv(race_info_list, DataType.SHUTUBA)
            self.logger.info(f"race_info_listを保存しました")
        if horse_info_list:
            self._save_to_csv(horse_info_list, DataType.HISTORY)
            self.logger.info(f"horse_info_listを保存しました")
        if race_result_list:
            self._save_to_csv(race_result_list, DataType.RESULT)
            self.logger.info(f"race_result_listを保存しました")

        self.logger.info("取得と保存が終了しました")

    def _get_target_race_ids(self, date, course_codes, race_nums) -> list:
        """
        目的のレースIDリストを返す
        """
        kaisai_ids = []
        filtered_kaisai_ids = []
        # 地方競馬、中央競馬、両方を回す
        for is_nar in [True, False]:
            kaisai_ids += self._get_kaisai_ids(date, is_nar)
        # 指定がある場合はフィルタリングする
        if kaisai_ids and (course_codes or race_nums):
            filtered_kaisai_ids = self._get_filtered_kaisai_ids(kaisai_ids, course_codes, race_nums)
            self.logger.info(f"kaisai_ids {len(kaisai_ids)}件から filtered_kaisai_ids {len(filtered_kaisai_ids)}にフィルタリングしました")
            return filtered_kaisai_ids
        else:
            return kaisai_ids

    def _get_kaisai_ids(self, date: str, is_nar: bool):
        """
        指定日の開催IDリスト（10桁）を取得
        例: 2026470324 (2026年 47:名古屋 03回 24日目)
        """
        url = get_top_page_url(date, is_nar)
        html = self.client.get_html(url)
        
        kaisai_ids = self.parser.extract_race_ids(html)
        
        self.logger.info(f"kaisai_ids: {len(kaisai_ids)}件取得しました")
        return kaisai_ids

    def _get_filtered_kaisai_ids(self, kaisai_ids: list, course_codes: list, race_nums: list) -> list:
        """
        フィルタリングしたレースIDを返す
        """
        # 帯広と不明は除外
        filtered_ids = filter_race_ids_exclude_course(kaisai_ids)
        # コースでフィルタリング
        if course_codes:
            filtered_ids = filter_race_ids_by_course(filtered_ids, course_codes)
        if race_nums:
            filtered_ids = filter_race_ids_by_number(filtered_ids, race_nums)
        return filtered_ids

    def _get_race_infos_from_ids(self, race_ids, only_race: bool):
        """
        目的の出馬表、各馬のIDの取得
        """
        race_infos = []
        horse_ids = []
        for r_id in race_ids:
            r_info, h_ids = self._collect_race_at(r_id)
            if r_info:
                race_infos += r_info
                horse_ids += h_ids
        return race_infos, horse_ids

    def _get_horse_infos_from_ids(self, horse_ids: list):
        """
        目的の馬の過去データの取得
        """
        history_dfs = []
        sire_names_list = []
        for h_id in horse_ids:
            if h_id not in self.processed_horse_ids:
                h_url = get_horse_url(h_url)
                h_html = self.client.get_html(h_url)
                df, sire_names = self.parser.parse_horse_history(h_html, h_id)
                self.logger.info(f"get {h_id} data >> {df}")
                if sire_names:
                    sire_names_list.append(sire_names)
                if not df.empty:
                    history_dfs.append(df)
                    self.processed_horse_ids.add(h_id)
                time.sleep(1)
        return history_dfs, sire_names_list

    def _get_race_result_from_ids(self, race_ids):
        """
        目的のレース結果の取得
        """
        result_list = []
        for r_id in race_ids:
            result = []
            if result:
                result_list.append(result)
        return result_list

    def _collect_race_at(self, race_id):
        """
        特定の1レースに関する情報を取得する
        """
        url = get_race_url(race_id)
        html = self.client.get_html(url)
        race_info, horse_ids = self.parser.parse_race_page(html, race_id)
        return race_info, horse_ids

    def _save_to_csv(self, data_list: list, data_type: DataType):
        """
        データ形式をDataFrameにしてCSVで保存する
        """
        pass
        
    def _determine_target_date(self, input_date: str) -> str:
        """
        取得する日付の決定
        - 指定がある場合＞指定日を返す
        - 指定がない場合＞nowの日付を返す
        """
        return normalize_date_format(input_date if input_date else get_today_jst())
