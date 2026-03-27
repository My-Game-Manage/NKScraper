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
