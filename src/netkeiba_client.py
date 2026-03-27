# netkeibaアクセス用
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

class NetKeibaClient:
    def __init__(self, headless=True):
        self.driver = self._setup_driver(headless)
