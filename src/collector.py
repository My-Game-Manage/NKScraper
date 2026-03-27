# スクレイピング本体


class RaceDataCollector:
    def __init__(self, headless=True):
        self.driver = None
