from src.constants.master_data import JRA_MAX_COURSE_CODE
from src.constants.schema import NetkeibaDomain

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
    
def get_race_url(race_id: str, page_type: str = "result") -> str:
    """
    レースIDとページ種別からフルURLを生成する
    page_type: 'result', 'shutuba', 'odds' など
    """
    domain = get_netkeiba_domain(race_id)
    
    # ページ種別ごとのパス（netkeibaの仕様に合わせる）
    path_map = {
        "result": "race/result.html",
        "shutuba": "race/shutuba.html",
        "odds": "race/odds.html"
    }
    path = path_map.get(page_type, "race/result.html")
    
    return f"https://{domain}.netkeiba.com/{path}?race_id={race_id}"
    
def get_top_page_url(target_date: str, is_nar: bool = True) -> str:
    """
    日付から開催トップページのURLを生成する
    """
    domain = get_netkeiba_domain_by_is_nar(is_nar)
    return f"https://{domain}.netkeiba.com/top/?kaisai_date={target_date}"
