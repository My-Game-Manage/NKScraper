# src/utils/logger.py
import logging
import os
from datetime import datetime

def setup_logger(name: str, log_dir: str = "logs"):
    """
    ロガーを初期化し、コンソールとファイルの両方に出力する設定を行う
    """
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO) # どのレベル以上を記録するか

    # すでにハンドラが設定されている場合は重複しないように戻す
    if logger.handlers:
        return logger

    # 出力フォーマットの設定（時刻, レベル, メッセージ）
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. コンソール出力用の設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. ファイル出力用の設定 (日付ごとのファイル名にする)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
