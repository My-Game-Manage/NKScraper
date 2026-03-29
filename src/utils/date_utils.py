import pandas as pd
from datetime import datetime, timedelta, timezone

def normalize_date_format(date_val) -> str:
    """
    あらゆる日付形式を 8桁の文字列ID 'YYYYMMDD' に変換する
    """
    if not date_val:
        return ""

    # すでに 20260327 形式の文字列ならそのまま返す
    if isinstance(date_val, str) and len(date_val) == 8 and date_val.isdigit():
        return date_val

    # datetimeオブジェクトの場合
    if isinstance(date_val, datetime):
        return date_val.strftime('%Y%m%d')

    # それ以外（ハイフンあり文字列など）
    date_str = str(date_val).strip()
    # 数字だけを抽出
    normalized = "".join(filter(str.isdigit, date_str))
    
    return normalized
    
def get_today_jst() -> str:
    """
    現在の日本時間を 'YYYYMMDD' 形式で返す
    """
    # UTC+9時間（日本時間）のタイムゾーンを定義
    # 現在時刻をJSTで取得
    return datetime.now(timezone(timedelta(hours=9), 'JST')).strftime('%Y%m%d')

def time_to_seconds(time_str):
    """'1:25.2' -> 85.2, '59.9' -> 59.9 への変換"""
    if pd.isna(time_str) or not isinstance(time_str, str) or time_str == "**":
        return None
    try:
        if ':' in time_str:
            m, s = time_str.split(':')
            return int(m) * 60 + float(s)
        return float(time_str)
    except: return None

def format_date_strict(date_val) -> str:
    if isinstance(date_val, datetime):
        # datetime型の場合はそのまま返す
        return date_val

    # 文字列を一度日付オブジェクトに変換してから再フォーマット
    dt = datetime.strptime(date_val, "%Y%m%d")
    return dt.strftime("%Y/%m/%d")
