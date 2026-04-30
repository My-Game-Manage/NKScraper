# netkeibaアクセス用
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

from src.utils.logger import setup_logger

import logging

# ロガーの取得（__name__ はファイル名/モジュール名になる）
logger = logging.getLogger(__name__)


class NetKeibaClient:
    def __init__(self, headless=True):
        """
        初期化： Driverの初期化
        """
        # クラス名を名前としてロガーを作成
        #logger = setup_logger("NetkeibaClient")
        
        # ドライバー初期化
        self.driver = self._setup_driver(headless)        

    def quit(self):
        """
        Driverの正常終了
        """
        if self.driver:
            self.driver.quit()

    def get_html(self, url: str, retry_count=3) -> str:
        """リトライ機能付きのページ取得"""
        for i in range(retry_count):
            try:
                self.driver.get(url)
                time.sleep(1) # 安定させるための待機
                return self.driver.page_source
            except WebDriverException as e:
                if i < retry_count - 1:
                    time.sleep(3)
                    continue
        return ""

    def _setup_driver(self, headless):
        """
        Driverの初期化
        """
        logger.info("Driverの初期化中...")
        
        options = Options()
        logger.info(f"テストしてます")
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.page_load_strategy = 'eager'
        
        logger.info(f"Option終わり")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        
        logger.info("Driverの準備ができました")
        return driver
