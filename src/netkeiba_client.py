# netkeibaアクセス用
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

from src.utils.logger import setup_logger

class NetKeibaClient:
    def __init__(self, headless=True):
        """
        初期化： Driverの初期化
        """
        # クラス名を名前としてロガーを作成
        self.logger = setup_logger("NetkeibaClient")
        
        # ドライバー初期化
        self.driver = self._setup_driver(headless)        

    def quit(self):
        """
        Driverの正常終了
        """
        if self.driver:
            self.driver.quit()

    def _setup_driver(self, headless):
        """
        Driverの初期化
        """
        self.logger.info("Driverの初期化中...")
        
        options = Options()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.page_load_strategy = 'eager'
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(30)
        
        self.logger.info("Driverの準備ができました")
        return driver
