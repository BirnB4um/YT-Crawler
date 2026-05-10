import requests
import json
import os
import random
import re
import time
import traceback

from logger import CrawlLogger
from Exceptions import *
from Selector import *
from ScoreFunction import *
from Models import Models
from Scraper import YT_Scraper
from Datapack import Datapack
from SQLSaver import SQLSaver

logger = CrawlLogger().logger


class Crawler():


    def __init__(
            self,
            run_name:str="default",
            save_folder:str="crawl_results",
            selector:Selector=WeightedRandomTopKSelector(),
            score_function:ScoreFunction=SmallVideoScoreFunction()
        ):
        
        os.makedirs(os.path.join(save_folder, run_name), exist_ok=True)

        logger.info("Initializing Crawler...")
        Models()
        
        self.run_name = run_name
        self.scraper = YT_Scraper()
        
        self.selector = selector
        self.score_function = score_function
        
        self.squash_interval = 10_000
        self.sql_saver = SQLSaver(db_path=os.path.join(save_folder, run_name, "videos.db"))
        

    def _get_sleep_time(self):
        sleep_time = random.uniform(5, 10)
        return sleep_time
    
    

    def _crawl_generator(self, start_id:str):
        datapack = Datapack()
        
        vid = VideoData(video_id=start_id)
        
        empty_rec_counter = 0
        
        idx = 0
        while True:
            idx += 1
            start_time = time.time()

            recommendations = self.scraper.get_recommended_videos(vid.video_id)
            
            self.sql_saver.save_videos(vid, recommendations)
            
            if len(recommendations) > 0:
                empty_rec_counter = 0
            else:
                empty_rec_counter += 1
                if empty_rec_counter == 3:
                    logger.warning("3 consecutive videos with no recommendations found.")
                    self.scraper.renew_session()
                elif empty_rec_counter >= 6:
                    raise NoVideosFound(f"No recommendations found after 6 attempts. Stopping crawl.")
                
                
            recommendations = datapack.filter_blacklist(recommendations)
                            
            for v in recommendations:
                v.process(vid)
                
                
            t = time.time()
            recommendations = self.score_function.score(vid, recommendations, inplace=True)
            # logger.debug(f"Scored {len(recommendations)} videos in {time.time() - t:.1f} seconds.")
            
            
            datapack.add_videos(recommendations)
            
            # if idx % 50 == 0:
            #     for video in recommendations:
            #         logger.debug(f"{video.video_id} {video.score}")
            #     logger.debug(f"Pickset size: {len(datapack.pickset)} ({len(datapack.trashset)} in trash).")
            #     ps = [v.score.localized_score for v in datapack.pickset]
            #     quant = np.quantile(ps, [0, 0.25, 0.5, 0.75, 0.9, 1])
            #     logger.debug(f"Pickset quantiles: {quant}")
            #     mean_score = np.mean(ps)
            #     logger.debug(f"Pickset mean score: {mean_score:.4f}")
            #     logger.debug(f"{len([s for s in ps if s > 0])} in pickset with score > 0")
            #     max_depth = max([v.tree_depth for v in datapack.pickset]) if datapack.pickset else 0
            #     logger.debug(f"Max tree depth in pickset: {max_depth}")
            
            if idx % self.squash_interval == 0:
                logger.info("Squashing datapack...")
                datapack.squash()

            vid = self.selector.select(datapack)
            

            time_taken = time.time() - start_time
            time.sleep(max(0, self._get_sleep_time() - time_taken))

            yield vid.video_id



    def crawl(self, start_id:str, depth:int=10):
        
        try:
            logger.info(f"Starting crawl from {start_id} with depth {depth}...")
            for i, id in enumerate(self._crawl_generator(start_id)):
                if i >= depth-1:
                    break

        except CrawlerException as e:
            pass
        except Exception as e:
            logger.error(f"An error occurred: {e}\n{traceback.format_exc()}")

        

    def infinite_crawl(self, start_id:str):
        try:
            logger.info(f"Starting infinite crawl from {start_id}...")
            for id in self._crawl_generator(start_id):
                pass

        except CrawlerException as e:
            pass
        except Exception as e:
            logger.error(f"An error occurred: {e}\n{traceback.format_exc()}")
            
            
    def conditional_crawl(self, start_id:str, condition_function:callable):
        """
        Crawl until condition_function returns False.
        """
        try:
            logger.info(f"Starting conditional crawl from {start_id}...")
            for id in self._crawl_generator(start_id):
                if not condition_function():
                    logger.info("Condition function returned False. Stopping crawl.")
                    break

        except CrawlerException as e:
            pass
        except Exception as e:
            logger.error(f"An error occurred: {e}\n{traceback.format_exc()}")
