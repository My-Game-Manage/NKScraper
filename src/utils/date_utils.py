from datetime import datetime

def to_date_id(date_val) -> str:
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
