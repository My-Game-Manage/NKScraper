"""
collector.py の概要
このクラスの主な責務は以下の3つです。

依存クラスの集約: NetKeibaClient（通信）、DataParser（解析）、DataNormalizer（修正）を束ねる。

実行フローの制御: 「ID取得 → HTML取得 → パース → 正規化 → 保存」という一連の流れを実行する。

環境管理: 保存先ディレクトリの作成や、重複データのチェック（キャッシュ管理）を行う。
"""

import os
from src.netkeiba_client import NetKeibaClient
from src.parser import DataParser
from src.normalizer import DataNormalizer  # 先ほど提案した正規化クラス

DEFAULT_BASE_DIR = 'data'

class RaceDataCollector:
    def __init__(self, headless: bool = True, base_dir: str = DEFAULT_BASE_DIR):
        """
        初期化: 必要なコンポーネントのインスタンス化とディレクトリ準備
        """
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
        # 1. レースID一覧を取得（client）
        # 2. 各レースの処理
        # 2-1. ソース取得（client）
        # 2-2. 欲しい情報採取（）
        # 2-3. データ整形・表記ゆれ等の修正（normalizer）
        # 3. CSVとして保存
        pass
