# 正規化用

import pandas as pd

from src.constants.schema import RaceCol, NetkeibaPageType
from src.utils.date_utils import time_to_seconds, format_date_strict

SAVE_COLUMNS_ORDER = {
    NetkeibaPageType.SHUTUBA: [
        RaceCol.DATE,             # date
        RaceCol.COURSE,           # course
        RaceCol.WEATHER,          # weather
        RaceCol.RACE_NUMBER,      # race_number
        RaceCol.RACE_NAME,        # race_name
        RaceCol.SURFACE,          # surface
        RaceCol.DISTANCE,         # distance
        RaceCol.TRACK_CONDITION,  # track_condition
        RaceCol.NUM_HORSES,       # num_horses
        RaceCol.BRACKET_NUM,      # bracket_number
        RaceCol.HORSE_NUM,        # horse_number
        RaceCol.HORSE_NAME,       # horse_name
        RaceCol.FATHER,           # father_name
        RaceCol.MOTHER,           # mother_name
        RaceCol.SEX,              # sex
        RaceCol.AGE,              # age
        RaceCol.WEIGHT_CARRIED,   # weight_carried
        RaceCol.JOCKEY,           # jockey
        RaceCol.STABLE,           # stable
        RaceCol.HORSE_WEIGHT,     # horse_weight
        RaceCol.WEIGHT_DIFF,      # weight_diff
        RaceCol.HORSE_ID          # horse_id
    ],
    NetkeibaPageType.HORSE: [
        # '馬ID', '馬名', '日付', '開催', '天気', 'R', 'レース名', '頭数', '枠番', '馬番',
        # 'オッズ', '人気', '着順', '騎手', '斤量', '種別', '距離', '馬場',
        # 'タイム', '着差', '通過', '上り', '体重', '体重増減', '勝ち馬(2着馬)', '賞金'
        RaceCol.HORSE_ID, RaceCol.HORSE_NAME, RaceCol.DATE, RaceCol.COURSE, 
        RaceCol.WEATHER, RaceCol.RACE_NUMBER, RaceCol.RACE_NAME, RaceCol.NUM_HORSES, 
        RaceCol.BRACKET_NUM, RaceCol.HORSE_NUM, RaceCol.ODDS, RaceCol.POPULARITY, 
        RaceCol.RANK, RaceCol.JOCKEY, RaceCol.WEIGHT_CARRIED, RaceCol.SURFACE, 
        RaceCol.DISTANCE, RaceCol.TRACK_CONDITION, RaceCol.TIME, RaceCol.MARGIN, 
        RaceCol.PASSING_ORDER, RaceCol.LAST_3F, RaceCol.HORSE_WEIGHT, 
        RaceCol.WEIGHT_DIFF, RaceCol.WINNER_NAME, RaceCol.PRIZE
    ],
    NetkeibaPageType.RESULT: [
        RaceCol.DATE,             # date
        RaceCol.COURSE,           # course
        RaceCol.WEATHER,          # weather
        RaceCol.RACE_NUMBER,      # race_number
        RaceCol.RACE_NAME,        # race_name
        RaceCol.SURFACE,          # surface
        RaceCol.DISTANCE,         # distance
        RaceCol.TRACK_CONDITION,  # track_condition
        RaceCol.NUM_HORSES,       # num_horses
        RaceCol.RANK,             # rank
        RaceCol.BRACKET_NUM,      # bracket_number
        RaceCol.HORSE_NUM,        # horse_number
        RaceCol.HORSE_NAME,       # horse_name
        RaceCol.SEX,              # sex
        RaceCol.AGE,              # age
        RaceCol.WEIGHT_CARRIED,   # weight_carried
        RaceCol.JOCKEY,           # jockey
        RaceCol.TIME,             # time
        RaceCol.MARGIN,           # margin
        RaceCol.POPULARITY,       # popularity
        RaceCol.ODDS,             # odds
        RaceCol.LAST_3F,          # last_3f
        RaceCol.PASSING_ORDER,    # passing_order
        RaceCol.STABLE,           # stable
        RaceCol.HORSE_WEIGHT,     # horse_weight
        RaceCol.WEIGHT_DIFF,      # weight_diff
        RaceCol.HORSE_ID          # horse_id
    ],
}

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
    def convert_date_to_strict(df: pd.DataFrame) -> pd.DataFrame:
        """
        '20260320'のような日付を'2026/03/20'に変換して上書き
        """
        # 日付カラムが存在する場合のみ実行
    if RaceCol.DATE in df.columns:
        df[RaceCol.DATE] = df[RaceCol.DATE].apply(format_date_strict)
    return df

    @staticmethod
    def ensure_dataframe(data) -> pd.DataFrame:
        """
        入力がリストならDataFrameに変換し、DataFrameならそのまま返す。
        リストの中身がDataFrameの場合は結合してDataFrameにして返す
        それ以外（Noneなど）の場合は空のDataFrameを返す。
        """
        if isinstance(data, pd.DataFrame):
            return data
    
        if isinstance(data, list):
            if isinstance(data[0], pd.DataFrame):
                return pd.concat(data)
            else:
                return pd.DataFrame(data)
    
        # データが空、または想定外の型の場合
        return pd.DataFrame()
    
    @staticmethod
    def normalize_horse_history_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        スペース等を除去する
        """
        # 1. カラム名のクリーニング（スペース除去）
        df.columns = [c.replace(' ', '').replace('　', '') for c in df.columns]
        
        # 2. 全要素のクリーニング（Pandas 2.1.0+ 対応の map を使用）
        df = df.map(lambda x: x.strip().replace(' ', '').replace('　', '') if isinstance(x, str) else x)

        return df

    @staticmethod
    def normalize_columns(df: pd.DataFrame, data_type: NetkeibaPageType) -> pd.DataFrame:
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

        # 5. 日付をYYYY/MM/DDに書き換え
        df = DataNormalizer.convert_date_to_strict(df)

        # 5. 変換後の英語名で、推奨される列順序を定義
        # (RaceCol の定数を使うことで、タイポを防ぎます)
        target_order = SAVE_COLUMNS_ORDER.get(data_type, NetkeibaPageType.SHUTUBA)

        # 存在するカラムのみで順序を整える（存在しない列があってもエラーにならないようにする）
        existing_cols = [c for c in target_order if c in df.columns]
        
        return df[existing_cols]
