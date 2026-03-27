# main.py

import argparse
from src.collector import RaceDataCollector

def _get_normalized_race_num(race_num) -> int:
  return int(race_num) if (race_num and str(race_num).isdigit()) else None

def main():
    arg_parser = argparse.ArgumentParser(description="NetKeiba Scraper")
    arg_parser.add_argument("--date", default="", help="YYYYMMDD形式で日付指定")
    arg_parser.add_argument("--course", default="", help="会場名指定")
    arg_parser.add_argument("--race_num", default="", help="レース番号")
    arg_parser.add_argument("--result", action="store_true", default="", help="結果の方を取得する")
    arg_parser.add_argument("--only_race", action="store_true", help="出馬表のみ更新（過去履歴をスキップ）")
    args = arg_parser.parse_args()

    r_num = _get_normalized_race_num(args.race_num)

    collector = RaceDataCollector(headless=True)
    try:
        collector.run(
          date=args.date,
          course=args.course,
          race_num=r_num,
          is_result=args.result,
          only_race=args.only_race
        )
    finally:
        collector.client.quit()

if __name__ == "__main__":
    main()
