import sys
sys.path.append("../src")

from logger import CrawlLogger

debug = True
run_name = "test_6"

logger = CrawlLogger(
    crawl_name=run_name,
    log_folder="../crawl_results/",
    console=True,
    debug=debug
).logger

from Crawler import Crawler
from ScoreFunction import *
from Selector import *

crawler = Crawler(
    run_name=run_name,
    save_folder="../crawl_results",
    selector=WeightedRandomTopKSelector(k=20),
    score_function=SmallVideoScoreFunction()
)

id = "vJnILWgmPcI"

crawler.infinite_crawl(start_id=id)

# crawler.crawl(start_id=id, depth=100)

logger.info("Crawling finished.")