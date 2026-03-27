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

    def fetch_kaisai_ids(self, target_date: str, is_nar: bool) -> list:
        """
        指定日の開催IDリスト（10桁）を取得
        例: 2026470324 (2026年 47:名古屋 03回 24日目)
        """
        domain = 'nar' if is_nar else 'race'
        url = f"https://{domain}.netkeiba.com/top/race_list.html?kaisai_date={target_date}"
        html = self.get_html(url)
        
        # 開催ID（10桁の数字）を抽出する正規表現
        # 地方競馬URL例: kaisai_id=2026480324
        pattern = r'kaisai_id=(\d{10})'
        found_ids = re.findall(pattern, html)
        print(f"found_ids: {found_ids}")
        
        # 重複を除去してソートして返す
        return sorted(list(set(found_ids)))

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
