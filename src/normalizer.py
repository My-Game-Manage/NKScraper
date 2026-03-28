# 正規化用

import pandas as pd
from src.constants.schema import RaceCol
from src.utils.date_utils import time_to_seconds

class DataNormalizer:
    @staticmethod
    def convert_time_to_seconds(df: pd.DataFrame) -> pd.DataFrame:
        """
        '1:30.3' のようなタイム文字列を秒(float)に変換して上書きする
        """
        # タイムカラムが存在する場合のみ実行
        if RaceCol.TIME in df.columns:
            # Series.apply を使って全行一括処理
            df[RaceCol.TIME] = df[RaceCol.TIME].apply(time_to_seconds)
            
        return df
        
    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        日本語カラム名を schema.py の定義に基づき英語に変換し、順序を整える
        """
        # 1. RaceCol.TO_JAPANESE を反転させて {日本語: 英語} のマップを作る
        # 例: {"馬ID": "horse_id", "馬名": "horse_name", ...}
        mapping = {v: k for k, v in RaceCol.TO_JAPANESE.items()}
        
        # 2. 既存のコードにある表記揺れ（'R' や '通過' など）を補完
        # schemaの定義とCSVのヘッダーが微差ある場合に対応
        mapping.update({
            "R": RaceCol.RACE_NUMBER,
            "通過": RaceCol.PASSING_ORDER,
            "上り": RaceCol.LAST_3F,
            "体重": RaceCol.HORSE_WEIGHT,
            "勝ち馬(2着馬)": RaceCol.WINNER_NAME,
            "後3F": RaceCol.LAST_3F,  # レース結果CSV用
            "単勝": RaceCol.WIN_ODDS,   # レース結果CSV用
        })

        # 3. カラム名の置換を実行
        df = df.rename(columns=mapping)

        # 4. タイムを秒換算に書き換え
        df = DataNormalizer.convert_time_to_seconds(df)
        print(f"normalize rename > time_to_sec df: {df}")

        # 5. 変換後の英語名で、推奨される列順序を定義
        # (RaceCol の定数を使うことで、タイポを防ぎます)
        target_order = [
            RaceCol.HORSE_ID, RaceCol.HORSE_NAME, RaceCol.DATE, RaceCol.COURSE, 
            RaceCol.WEATHER, RaceCol.RACE_NUMBER, RaceCol.RACE_NAME, RaceCol.NUM_HORSES, 
            RaceCol.BRACKET_NUM, RaceCol.HORSE_NUM, RaceCol.ODDS, RaceCol.POPULARITY, 
            RaceCol.RANK, RaceCol.JOCKEY, RaceCol.WEIGHT_CARRIED, RaceCol.SURFACE, 
            RaceCol.DISTANCE, RaceCol.TRACK_CONDITION, RaceCol.TIME, RaceCol.MARGIN, 
            RaceCol.PASSING_ORDER, RaceCol.LAST_3F, RaceCol.HORSE_WEIGHT, 
            RaceCol.WEIGHT_DIFF, RaceCol.WINNER_NAME, RaceCol.PRIZE
        ]

        # 存在するカラムのみで順序を整える（存在しない列があってもエラーにならないようにする）
        existing_cols = [c for c in target_order if c in df.columns]
        
        return df[existing_cols]
