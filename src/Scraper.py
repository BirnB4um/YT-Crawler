import requests
import json
import os
import random
import re
import time
from bs4 import BeautifulSoup
import traceback

from logger import CrawlLogger
from Exceptions import *
from VideoData import VideoData

logger = CrawlLogger().logger

class YT_Scraper():

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.105 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.114 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.3240.50 Safari/537.36 Edg/136.0.3240.50",

        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.114 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.7049.114 Safari/537.36",

        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:138.0) Gecko/20100101 Firefox/138.0",
    ]


    def __init__(self):

        self.session_started = 0
        self.session = None
        self.MAX_SESSION_LENGTH = 60 * 60 * 2 # 2 hours
        self.MAX_RETRIES = 3
        self.renew_session()


        self.BASE_URL = "https://www.youtube.com/watch?v="

        self.video_filter_type = "htmlparser" # "regex", "htmlparser"


    def _is_session_closed(self):
        return not bool(self.session.adapters)
    
    def renew_session(self):
        logger.info("Renewing session...")
        self.session = requests.Session()

        self.session.cookies
        self.session.headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
        }
        # self.session.cookies.set("CONSENT", "YES+cb", domain=".youtube.com")

        self.session_started = time.time()


    def get_yt_page(self, id):
        url = self.BASE_URL + id

        # reset session if closed
        if self._is_session_closed():
            logger.info("Session was closed. Creating a new session...")
            self.renew_session()

        # refresh session if too old
        if time.time() > self.session_started + self.MAX_SESSION_LENGTH :
            self.renew_session()
            
        # rotate user agent
        if random.random() < 0.2:
            user_agent = random.choice(self.USER_AGENTS)
            self.session.headers["User-Agent"] = user_agent

        response = self.session.get(url, timeout=30)

        if response.status_code != 200:
            error_details = {
                "url": url,
                "status_code": response.status_code,
                "headers": response.headers,
                "content": response.content
            }
            raise BadStatusCode(response.status_code, details=error_details)
        

        if "text/html" not in response.headers.get("Content-Type"):
            raise WrongResponseFormat(response.headers['Content-Type'], details={
                "url": url,
                "headers": response.headers,
                "content": response.content
            })
        
        # TODO: maybe test for other stuff

        return response
    
    
    def _filter_only_next_ids(self, page, id) -> list[VideoData]:
        pattern = re.compile(r'watch\?v=([a-zA-Z0-9_-]{11})')
        matches = pattern.findall(page.text)
        matches = list(set(matches))
        # ids = {
        #     id:{
        #         "title": None,
        #         "views": None,
        #         "length": None,
        #         "channel": None
        #     } 
        #     for id in matches
        # }
        ids = [VideoData(video_id=id) for id in matches]
        return ids
    
    
    def _extract_videodata_from_block(self, block) -> VideoData:
        if "endScreenVideoRenderer" not in block:
                return None
        
        video_data = block["endScreenVideoRenderer"]

        video_id = video_data.get("videoId")
        if video_id is None:
            return None

        title = video_data.get("title", {}).get("simpleText")
        
        views = video_data.get("shortViewCountText", {}).get("simpleText")
        if views is None:
            views = video_data.get("shortViewCountText", {}).get("runs", [{}])[0].get("text")
            
        length = video_data.get("lengthInSeconds")
        
        channel = video_data.get("shortBylineText", {}).get("runs", [{}])[0].get("text")
        
        uploaded_str = video_data.get("publishedTimeText", {}).get("simpleText")
        
        

        if views is not None:
            try:
                views_str = views
                if "No views" in views_str:
                    views_str = "0"

                views_str = views_str.split(" ")[0].strip()
                views_str = views_str.replace(",", ".")
                
                if "K" in views_str:
                    views = int(float(views_str.replace("K", "")) * 1e3)
                elif "M" in views_str:
                    views = int(float(views_str.replace("M", "")) * 1e6)
                elif "B" in views_str:
                    views = int(float(views_str.replace("B", "")) * 1e9)
                else:
                    views = int(views_str.replace(".", "").replace(",", ""))
                
            except Exception as e:
                logger.error(f"Error while parsing views. Original views string: {views}. Error: {e}")
                views = None
                

        # NOTE: if length is None, video might be a live stream
        
        # if length is not None:
        #     try:
        #         total_seconds = 0
        #         parts = length.strip().split(":")[::-1]
        #         for i, part in enumerate(parts):
        #             total_seconds += int(part) * (60 ** i)
        #         length = total_seconds
        #     except Exception as e:
        #         logger.error(f"Error while parsing length. Original length string: {length}. Error: {e}")
        #         length = None
        

        if uploaded_str is not None:
            try:
                uploaded_digits = re.sub(r"[^\d]", "", uploaded_str)
                if uploaded_digits.isdigit():
                    uploaded_digits = int(uploaded_digits)

                    if "second" in uploaded_str:
                        uploaded = uploaded_digits
                    elif "minute" in uploaded_str:
                        uploaded = uploaded_digits * 60
                    elif "hour" in uploaded_str:
                        uploaded = uploaded_digits * 3600
                    elif "day" in uploaded_str:
                        uploaded = uploaded_digits * 86400
                    elif "week" in uploaded_str:
                        uploaded = uploaded_digits * 604800
                    elif "month" in uploaded_str:
                        uploaded = uploaded_digits * 2592000
                    elif "year" in uploaded_str:
                        uploaded = uploaded_digits * 31536000
                    else:
                        logger.error(f"Unknown time unit in uploaded string: {uploaded_str}")
                        uploaded = None

                    if uploaded is not None:
                        uploaded = int(time.time()) - uploaded

                else:
                    logger.error(f"Error while parsing uploaded time. Expected an integer, got {uploaded_digits}. Original uploaded string: {uploaded_str}")
                    uploaded = None
            except Exception as e:
                logger.error(f"Error while parsing uploaded time. Original uploaded string: {uploaded_str}. Error: {e}")
                uploaded = None


        # print(f"Video ID: {video_id}")
        # print(f"Title: {title}")
        # print(f"Channel: {channel}")
        # print(f"Length (seconds): {length}")
        # print(f"Views: {views}")
        # print(f"Uploaded: {uploaded} (original string: {uploaded_str})")

        return VideoData(
            video_id=video_id,
            title=title,
            channel=channel,
            views=views,
            length=length,
            uploaded=uploaded
        )

        
    
    def _filter_recommendation_data(self, page, id) -> list[VideoData]:
        soup = BeautifulSoup(page.content, "html.parser")
        
        data_block = None
        for script in soup.find_all("script"):
            if script.string and "ytInitialData" in script.string:
                match = re.search(r"ytInitialData\s*=\s*({.*?});", script.string, re.DOTALL)
                if match:
                    data_str = match.group(1)
                    try:
                        data_block = json.loads(data_str)
                    except json.JSONDecodeError as e:
                        raise ParsingError(data_str, details={
                            "error": str(e),
                            "video_id": id,
                            "page": page.text
                        })
                    break

        if data_block is None:
            raise NoDataFound("Couldn't find ytInitialData in the page.", details={
                "video_id": id,
                "page": page.text
            })
        
        try:
            # if video is unavailable, return empty recommendations
            current_video = data_block["contents"]["twoColumnWatchNextResults"]["results"]
            if "video unavailable" in json.dumps(current_video, ensure_ascii=False).lower():
                logger.warning(f"Video {id} is unavailable. Returning empty recommendations.")
                return []
        except Exception as e:
            pass

        try:
            # results_block = data_block["contents"]["twoColumnWatchNextResults"]["secondaryResults"]["secondaryResults"]["results"]
            results_block = data_block["playerOverlays"]["playerOverlayRenderer"]["endScreen"]["watchNextEndScreenRenderer"]
            if "results" not in results_block:
                logger.warning(f"No recommendations found for {id} in the end screen.")
                return []
            results_block = results_block["results"]
        except Exception as e:
            raise UnexpectedFormat("Couldn't find the recommended videos in the page.", details={
                "error": str(e),
                "video_id": id,
                "data_block": data_block
            })

        next_videos = []
        try:
            for entry in results_block:
                video_data = self._extract_videodata_from_block(entry)
                if video_data is not None:
                    next_videos.append(video_data)
                
        except Exception as e:
            raise UnexpectedFormat("Couldn't find the video data in the page.", details={
                "error": str(e),
                "video_id": id,
                "page": page.text,
                "data_block": data_block
            })

        return next_videos


    def filter_next_videos(self, page, id) -> list[VideoData]:
        
        if self.video_filter_type == "htmlparser":
            try:
                next_videos = self._filter_recommendation_data(page, id)
            except CrawlerException as e:
                raise e
            except Exception as e:
                raise CrawlerException("An unexpected error occurred while filtering next videos (htmlparser).", details={
                    "error": str(e),
                    "video_id": id,
                    "page": page.text
                })
            
            return next_videos
            

        elif self.video_filter_type == "regex":
            try:
                next_videos = self._filter_only_next_ids(page)
            except CrawlerException as e:
                raise e
            except Exception as e:
                raise CrawlerException("An unexpected error occurred while filtering next videos (regex).", details={
                    "error": str(e),
                    "video_id": id,
                    "page": page.text
                })
            
            return next_videos
        
        return []
    

    def get_recommended_videos(self, id):
        """
        Returns next videos. If a fatal error occurs, raises a CrawlerException.
        """
        
        
        num_tries = self.MAX_RETRIES
        for i in range(num_tries):
            try:
                page = self.get_yt_page(id)
                next_videos = self.filter_next_videos(page, id)
                return next_videos
            
            except BadStatusCode as e:
                if e.status_code in [400, 401, 403, 404, 410]:
                    logger.error(f"Bad status code: {e.status_code}. Exiting...")
                    raise e
                
                logger.warning(f"Bad status code: {e.status_code}. (try {i+1}/{num_tries})")
                time.sleep(60)

            except NoDataFound as e:
                logger.warning(f"No data found: {e}. (try {i+1}/{num_tries})")
                if i == 1:
                    self.renew_session()
                time.sleep(60)

            except UnexpectedFormat as e:
                logger.warning(f"Unexpected format: {e}. (try {i+1}/{num_tries})")
                if i == 1:
                    self.renew_session()
                time.sleep(120)

            except CrawlerException as e:
                raise e

            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout error: {e}. (try {i+1}/{num_tries})")
                time.sleep(60)

            except Exception as e:
                raise CrawlerException("An unexpected error occurred while fetching the page or filtering videos.", details={
                    "error": str(e),
                    "video_id": id
                })
            
            
        raise CrawlerException("Max retries reached. Could not fetch the page or filter videos.", details={
            "video_id": id
        })
            
    

        
