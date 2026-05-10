
from logger import CrawlLogger

debug = True
run_name = "test_1"

logger = CrawlLogger(
    crawl_name=run_name,
    log_folder="/opt/yt-crawler/crawl_results/",
    console=True,
    debug=debug
).logger

from Crawler import Crawler
from ScoreFunction import *
from Selector import *

from Notify import send_ntfy_message

crawler = Crawler(
    run_name=run_name,
    save_folder="/opt/yt-crawler/crawl_results",
    selector=WeightedRandomTopKSelector(k=20),
    score_function=SmallVideoScoreFunction()
)

id = "vJnILWgmPcI"

crawler.infinite_crawl(start_id=id)

# crawler.crawl(start_id=id, depth=100)

logger.info("Crawling finished.")

send_ntfy_message("furby-yt-crawler", f"YT-Crawling run '{run_name}' has stopped.", "YT-Crawler stopped")