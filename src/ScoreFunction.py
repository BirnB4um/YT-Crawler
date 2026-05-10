

from VideoData import VideoData
from Score import *
from Models import Models
from logger import CrawlLogger

logger = CrawlLogger().logger

import copy
import re
import numpy as np


def as_log(x:float) -> float:
    return max(MIN_SCORE, np.log10(max(1e-6, x)))



class ScoreFunction():
    
    def __init__(self):
        pass
    
    def score(self, parent_video:VideoData, videos:list[VideoData], inplace: bool = True) -> list[VideoData]:
        """
        compute video scores for a given parent video.  
        
        If inplace is True, the scores are written directly into the video objects.  
        Otherwise, a new list of VideoData objects with computed scores is returned.
        """
        raise NotImplementedError("ScoreFunction subclasses must implement the score method.")
    
    
    
    
class OnlyDepthScoreFunction(ScoreFunction):
    """
    score videos based only on their depth from the parent video
    """
    
    def __init__(self):
        super().__init__()
    
    
    def _score(self, parent_video:VideoData, video:VideoData) -> Score:
        s = Score()
        s.depth_score = np.log10(0.5) * video.tree_depth
        return s
    
    
    def score(self, parent_video:VideoData, videos:list[VideoData], inplace: bool = True) -> list[VideoData]:
        scored_videos = videos if inplace else copy.deepcopy(videos)
        for video in scored_videos:
            video.score = self._score(parent_video, video)                  
        return scored_videos
    
    
    
class SmallVideoScoreFunction(ScoreFunction):
    """
    score videos based on how small they are (view count, length, title, etc.)
    """
    
    def __init__(self, cache_size:int=1000):
        super().__init__()
        
        self.cache_size = cache_size
        self.embedding_cache = np.zeros((cache_size, Models().emb_dims), dtype=np.float32)
        self.embedding_cache[:, 0] = 1.0
        self.cache_index = 0
        
        self.target_languages = ["en", "de"]

        self.blacklist = [
            r"god",
            r"jesus",
            r"motivation",
            r"bible",
            r"[\[\(/\{]\s*free\s*[\]\)/\}]",
            r"type\s+beat",
            r"wedding",
            r"inspiration",
            r"mindset",
            r"speech",
            r"jordan\s+peterson",
            r"donald\s+trump",
            r"mel\s+robbin",
            r"–",
            r"\d+\s+signs?",
            r"top\s+\d+",
            r"unbox(ing)?",
            r"review",
            r"haul",
        ]

        
    def get_views_score(self, views:int) -> float:
        if views is None:
            return MIN_SCORE
        if views > 1000:
            return MIN_SCORE
        score = 0.5 ** (views / 200)
        score = as_log(score)
        return score
    
    
    def get_length_score(self, length:int) -> float:
        # length in seconds
        # min(1, 0.5^( (length/60-10) * 3/40))
        if length is None:
            return MIN_SCORE
        if length > 60*60*1 + 10: # 1 hour
            return MIN_SCORE
        score = min(1.0, 0.5 ** ((length/60 - 10) * 3/40))
        score = as_log(score)
        return score


    def get_title_language_score(self, title:str) -> float:
        def ascii_ratio(text:str):
            ascii_count = sum(1 for c in text if c.isascii() and not c.isspace())
            total_count = sum(1 for c in text if not c.isspace())
            return ascii_count / total_count if total_count > 0 else 0.0
        
        lang, prob = Models().predict_language(title.lower())

        if lang not in self.target_languages: # if not target language
            if prob > 0.5: # if high confidence
                return MIN_SCORE
            else: # maybe mix of multiple languages
                r = ascii_ratio(title)
                if r < 0.6:
                    return MIN_SCORE
                return as_log((r-0.6)/0.4)
        return MAX_SCORE
    
    
    def get_title_score(self, title:str) -> float:
        
        blacklist_score = 1.0
        for pattern in self.blacklist:
            if re.search(pattern, title, re.IGNORECASE):
                blacklist_score = 0.001
                break
        
        title_length_score = 1.0 if len(title) < 60 else 0.95**(len(title)-60)
        
        score = title_length_score * blacklist_score
        score = as_log(score)
        return score
    
    
    def get_title_similarity_score(self, parent:VideoData, video:VideoData) -> float:
        
        title = video.title
        if not title:
            return MAX_SCORE
                
        # compute embedding
        if video.embedding is None:
            emb = Models().embed_text(title) # [1, emb_dim]
            video.embedding = emb.flatten()
        
        # calculate similarity score
        sim = np.dot(self.embedding_cache, video.embedding.T).flatten() # [cache_size]
        distance = np.max(sim, axis=0)
        dist_score = 1-(distance/2 + 0.5)**5 # from [-1, 1] to [1, 0]
        dist_score = as_log(dist_score)
        
        return dist_score
    
    
    def get_same_channel_score(self, channel1:str, channel2:str) -> float:
        if not channel1 or not channel2:
            return MAX_SCORE
        return as_log(0.01) if channel1.strip().lower() == channel2.strip().lower() else MAX_SCORE
    
    
    def get_tree_depth_score(self, depth:int) -> float:
        # log10(0.5 ** depth) = log10(0.5) * depth
        score = np.log10(0.5) * depth
        return score
    
    
    def _score_absolute(self, video:VideoData) -> Score:
        s = Score()
        s.view_score = self.get_views_score(video.views)
        s.length_score = self.get_length_score(video.length)
        s.language_score = self.get_title_language_score(video.title)
        s.title_score = self.get_title_score(video.title)
        return s
    
    
    def _score(self, parent_video:VideoData, video:VideoData) -> Score:
        s = Score()
        s.view_score = self.get_views_score(video.views)
        s.length_score = self.get_length_score(video.length)
        s.language_score = self.get_title_language_score(video.title)
        s.title_score = self.get_title_score(video.title)
        s.similar_title_score = self.get_title_similarity_score(parent_video, video)
        s.same_channel_score = self.get_same_channel_score(parent_video.channel, video.channel)
        s.depth_score = self.get_tree_depth_score(video.tree_depth)
        return s
    
    
    def add_embedding_to_cache(self, embedding:np.ndarray) -> None:
        self.embedding_cache[self.cache_index] = embedding
        self.cache_index = (self.cache_index + 1) % self.cache_size
    
    
    def score(self, parent_video:VideoData, videos:list[VideoData], inplace: bool = True) -> list[VideoData]:
        
        # add parent embedding to cache
        if parent_video.embedding is not None:
            self.add_embedding_to_cache(parent_video.embedding)
        
        scored_videos = videos if inplace else copy.deepcopy(videos)
        for video in scored_videos:
            video.score = self._score(parent_video, video)                  
            # logger.debug(f"{video.video_id} {video.score}")
        return scored_videos