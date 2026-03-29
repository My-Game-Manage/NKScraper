class NetkeibaDomain:
    # ドメイン定義
    NAR = 'nar'
    JRA = 'race'

class NetkeibaPageType:
    # ページの分類
    SHUTUBA = 'shutuba'
    RESULT = 'result'
    HORSE = 'horse'
    JOCKEY = 'jockey'
    ODDS = 'odds'

class RaceCol:
    # --- 英語名定義 (プログラムで使用) ---
    HORSE_ID = "horse_id"
    HORSE_NAME = "horse_name"
    DATE = "date"
    COURSE = "course"
    WEATHER = "weather"
    RACE_NUMBER = "race_number"
    RACE_NAME = "race_name"
    NUM_HORSES = "num_horses"
    BRACKET_NUM = "bracket_number"
    HORSE_NUM = "horse_number"
    SEX = "sex"
    AGE = "age"
    JOCKEY = "jockey"
    WEIGHT_CARRIED = "weight_carried"
    SURFACE = "surface"
    DISTANCE = "distance"
    TRACK_CONDITION = "track_condition"
    TIME = "time"
    MARGIN = "margin"
    PASSING_ORDER = "passing_order"
    LAST_3F = "last_3f"
    ODDS = "odds"
    WIN_ODDS = "win_odds"
    POPULARITY = "popularity"
    RANK = "rank"
    STABLE = "stable"
    HORSE_WEIGHT = "horse_weight"
    WEIGHT_DIFF = "weight_diff"
    WINNER_NAME = "winner_name"
    PRIZE = "prize"
    FATHER = "father_name"
    MOTHER = "mother_name"
    # --- タグ処理用追加 ---
    RACE_DATA = "race_data"

    # --- 日本語戻しマッピング (表示・出力用) ---
    TO_JAPANESE = {
        HORSE_ID: "馬ID",
        HORSE_NAME: "馬名",
        DATE: "日付",
        COURSE: "開催",
        WEATHER: "天気",
        RACE_NUMBER: "レース番号",
        RACE_NAME: "レース名",
        NUM_HORSES: "頭数",
        BRACKET_NUM: "枠番",
        HORSE_NUM: "馬番",
        SEX: "性別",
        AGE: "年齢",
        JOCKEY: "騎手",
        WEIGHT_CARRIED: "斤量",
        SURFACE: "種別",
        DISTANCE: "距離",
        TRACK_CONDITION: "馬場",
        TIME: "タイム",
        MARGIN: "着差",
        PASSING_ORDER: "通過順",
        LAST_3F: "上り",
        ODDS: "オッズ",
        WIN_ODDS: "単勝オッズ",
        POPULARITY: "人気",
        RANK: "着順",
        STABLE: "厩舎",
        HORSE_WEIGHT: "馬体重",
        WEIGHT_DIFF: "体重増減",
        WINNER_NAME: "勝ち馬",
        PRIZE: "賞金",
        FATHER: "父馬",
        MOTHER: "母馬",
        RACE_DATA: "レース情報",
    }
