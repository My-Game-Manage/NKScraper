"""
collector.py の概要
このクラスの主な責務は以下の3つです。

1. 依存クラスの集約: NetKeibaClient（通信）、DataParser（解析）、DataNormalizer（修正）を束ねる。
2. 実行フローの制御: 「ID取得 → HTML取得 → パース → 正規化 → 保存」という一連の流れを実行する。
3. 環境管理: 保存先ディレクトリの作成や、重複データのチェック（キャッシュ管理）を行う。
"""

import os
from enum import Enum
from src.netkeiba_client import NetKeibaClient
from src.parser import DataParser
from src.normalizer import DataNormalizer  # 先ほど提案した正規化クラス
from src.utils.date_utils import normalize_date_format, get_today_jst
from src.utils.logger import setup_logger

class DataType(Enum):
    SHUTSUBA = "出馬表"
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
        
        # 2. パス・ディレクトリの設定
        self.base_dir = base_dir
        
        # ディレクトリがなければ作成する
        os.makedirs(self.base_dir, exist_ok=True)

        # 3. 実行状態の管理（同じ馬を何度も取得しないためのキャッシュなど）
        self.processed_horse_ids = set()

    def run(self, date=None, course=None, race_num=None, is_result: bool=False, only_race: bool=False):
        """
        メインの実行メソッド
        """
        self.logger.info("Collectorを実行開始します...")
        
        # 1. レースID一覧を取得（client）
        target_race_ids = self._get_target_race_ids(date, course, race_num)
        self.logger.info(f"target_race_ids: {len(target_race_ids)}件取得しました")

        # 2. 各レースの処理（client＆normalizer）＞ソース取得・情報取得・整形・表記修正
        race_info_list, horse_info_list, race_result_list = [], [], []
        if is_result:
            race_result_list = self._get_race_result_from_ids(target_race_ids)
            self.logger.info(f"race_result_list: {len(race_result_list)}件取得しました")
        else:
            race_info_list, horse_info_list = self._get_race_infos_from_ids(target_race_ids, only_race)
            self.logger.info(f"race_info_list: {len(race_info_list)}件取得しました")
            self.logger.info(f"horse_info_list: {len(horse_info_list)}件取得しました")
            
        # 3. CSVとして保存
        if race_info_list:
            self._save_to_csv(race_info_list, DataType.SHUTSUBA)
            self.logger.info(f"race_info_listを保存しました")
        if horse_info_list:
            self._save_to_csv(horse_info_list, DataType.HISTORY)
            self.logger.info(f"horse_info_listを保存しました")
        if race_result_list:
            self._save_to_csv(race_result_list, DataType.RESULT)
            self.logger.info(f"race_result_listを保存しました")
        print("終了しました")

    def _get_target_race_ids(self, date, course, race_num) -> list:
        """
        目的のレースIDリストを返す
        """
        kaisai_ids = []
        filtered_kaisai_ids = []
        # 地方競馬、中央競馬、両方を回す
        for is_nar in [True, False]:
            kaisai_ids = self.client.get_kaisai_ids(date, is_nar)
            if kaisai_ids:
                filtered_kaisai_ids += self._get_filtered_kaisai_ids(kaisai_ids, is_nar)
        return filtered_kaisai_ids

    def _get_filtered_kaisai_ids(self, kaisai_ids, is_nar: bool):
        """
        フィルタリングしたレースIDを返す
        """
        return []

    def _get_race_infos_from_ids(self, race_ids, only_race: bool):
        """
        目的の出馬表、各馬の過去データの取得
        """
        return [], []

    def _get_race_result_from_ids(self, race_ids):
        """
        目的のレース結果の取得
        """
        return []

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
