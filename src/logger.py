import logging
from logging.handlers import RotatingFileHandler
import os

from Singleton import SingletonMeta


class CrawlLogger(metaclass=SingletonMeta):
    
    def __init__(self, crawl_name: str = "default", log_folder: str = "logs", console: bool = True, debug: bool = False):
        log_path = os.path.join(log_folder, crawl_name)
        os.makedirs(log_path, exist_ok=True)
        
        self.logger = logging.getLogger("crawllogger")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        
        fh = RotatingFileHandler(os.path.join(log_path, "crawl.log"), maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        fh.setLevel(logging.DEBUG if debug else logging.INFO)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        if console:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG if debug else logging.INFO)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
