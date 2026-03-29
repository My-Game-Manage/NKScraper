from src.constants.master_data import JYO_NAME_MAP, JRA_MAX_COURSE_CODE, EXCLUDE_COURSES
from src.constants.schema import NetkeibaDomain, NetkeibaPageType, RaceCol

def is_nar_id(race_id: str) -> bool:
    """
    IDから地方競馬か中央競馬か判定する
    """
    if not race_id or len(str(race_id)) < 6:
        return False
    try:
        course_code = int(str(race_id)[4:6])
        return course_code > JRA_MAX_COURSE_CODE
    except:
        return False
      
def get_netkeiba_domain(race_id: str) -> str:
    """
    レースIDから適切なドメイン (race または nar) を返す
    """
    if not race_id or len(str(race_id)) < 6:
        return NetkeibaDomain.JRA # "race" # デフォルト
    
    try:
        # IDの5-6文字目が場所コード
        course_code = int(str(race_id)[4:6])
        
        # 10以下なら中央(race)、11以上なら地方(nar)
        if course_code <= JRA_MAX_COURSE_CODE:
            return NetkeibaDomain.JRA
        else:
            return NetkeibaDomain.NAR
    except (ValueError, IndexError):
        return NetkeibaDomain.JRA

def get_netkeiba_domain_by_is_nar(is_nar: bool) -> str:
    """
    is_narからドメイン取得
    """
    return NetkeibaDomain.NAR if is_nar else NetkeibaDomain.JRA
    
def get_race_url(race_id: str, page_type: NetkeibaPageType=NetkeibaPageType.SHUTUBA) -> str:
    """
    レースIDとページ種別からフルURLを生成する
    page_type: 'result', 'shutuba', 'odds' など
    """
    domain = get_netkeiba_domain(race_id)
    
    # ページ種別ごとのパス（netkeibaの仕様に合わせる）
    path_map = {
        NetkeibaPageType.RESULT: "race/result.html",
        NetkeibaPageType.SHUTUBA: "race/shutuba.html",
        NetkeibaPageType.ODDS: "race/odds.html"
    }
    path = path_map.get(page_type, "race/result.html")
    
    return f"https://{domain}.netkeiba.com/{path}?race_id={race_id}"

def get_horse_url(horse_id: str) -> str:
    """
    馬IDからフルURLを生成する
    """
    return f"https://db.netkeiba.com/horse/{horse_id}"

def get_top_page_url(target_date: str, is_nar: bool = True) -> str:
    """
    日付から開催トップページのURLを生成する
    """
    domain = get_netkeiba_domain_by_is_nar(is_nar)
    return f"https://{domain}.netkeiba.com/top/?kaisai_date={target_date}"

def get_jyo_name(kaisai_id: str) -> str:
    """10桁または12桁のIDから会場名を特定"""
    if not kaisai_id or len(kaisai_id) < 6:
        return "不明"
            
    code = kaisai_id[4:6]
    # 定数から取得。なければ "不明" を返す
    return JYO_NAME_MAP.get(code, "不明")
    
def filter_race_ids_exclude_course(kaisai_ids: list) -> list:
    """
    レースIDリストから、除外対象を取り除く
    """
    valid_ids_list = []
    for k_id in kaisai_ids:
        actual_course = get_jyo_name(k_id)
        
        if actual_course in EXCLUDE_COURSES:
            print(f"スキップ中: {actual_course}({k_id}) は取得対象外です。")
            continue
        valid_ids_list.append(k_id)
    return valid_ids_list

def filter_race_ids_by_course(race_ids: list, target_course_codes: list) -> list:
    """
    レースIDリストの中から、指定した会場コードに合致するものだけを抽出する
    
    Args:
        race_ids (list): IDのリスト
        target_course_codes (list): ['44', '54'] のような場所コードのリスト
    
    Returns:
        list: フィルタリングされたレースIDリスト
    """
    if not race_ids:
        return []
    
    # 文字列として比較するために正規化 (54 -> "54")
    target_codes = [str(c).zfill(2) for c in target_course_codes]
    
    # IDの5-6文字目が場所コード
    filtered = [
        rid for rid in race_ids 
        if str(rid)[4:6] in target_codes
    ]
    
    return sorted(filtered)

def filter_race_ids_by_number(race_ids: list, target_nums: list) -> list:
    """
    レースIDリストの中から、指定したレース番号に合致するものだけを抽出する
    
    Args:
        race_ids (list): ['202654032801', '202654032802', ...] のようなIDリスト
        target_nums (list): [1, 11] のような取得したいレース番号のリスト
    
    Returns:
        list: フィルタリングされたレースIDリスト
    """
    if not race_ids:
        return []
    
    # 比較用にターゲット番号を文字列の2桁ゼロ埋めに変換しておく (1 -> "01")
    target_str_list = [str(n).zfill(2) for n in target_nums]
    
    # 末尾2桁がターゲットに含まれるものだけを抽出
    filtered = [
        rid for rid in race_ids 
        if str(rid)[-2:] in target_str_list
    ]
    
    return sorted(filtered)

def override_race_info_parents_name(race_info_list: list, sire_names_list: list) -> list:
    """
    馬の父母名を上書きする
    """
    # 手順1: Bを ID -> {父, 母} の辞書形式に変換する
    # {101: {'父': '...', '母': '...'}, 102: {...}} という形になります
    sire_map = {item[RaceCol.HORSE_ID]: item for item in sire_names_list}

    # 手順2: Aをループで回して、Bに同じIDがあれば上書きする
    for item_a in race_info_list:
        target_id = item_a[RaceCol.HORSE_ID]
        if target_id in sire_map:
            # B側に存在するデータで更新
            item_a[RaceCol.FATHER] = sire_map[target_id].get(RaceCol.FATHER, item_a[RaceCol.FATHER])
            item_a[RaceCol.MOTHER] = sire_map[target_id].get(RaceCol.MOTHER, item_a[RaceCol.MOTHER])
    return race_info_list

def split_race_info(text: str) -> list:
    """
    文字列を空白（全角・半角問わず）で区切ってリストで取得する
    """
    # split() は引数を指定しない場合、連続する空白や全角スペースも適切に処理します
    return text.split()
