
from Datapack import Datapack
from VideoData import VideoData

import random
import numpy as np


class Selector():
    
    def __init__(self):
        pass
    
    def select(self, datapack:Datapack) -> VideoData:
        """
        select next video from datapack
        """
        raise NotImplementedError("Selector subclasses must implement the select method.")
    
    
    
class GreedySelector(Selector):
    """
    select the highest scored video from datapack
    """
    
    def __init__(self):
        super().__init__()
    
    def select(self, datapack:Datapack) -> VideoData:
        return datapack.pick(0)
    
    

class RandomSelector(Selector):
    """
    select a random video from datapack
    """
    
    def __init__(self):
        super().__init__()
    
    def select(self, datapack:Datapack) -> VideoData:
        if len(datapack.pickset) == 0:
            return datapack.pick(0)
        index = random.randint(0, len(datapack.pickset) - 1)
        return datapack.pick(index)
    
    
    
class RandomTopKSelector(Selector):
    """
    select a random video from the top K scored videos in datapack
    """
    
    def __init__(self, k:int=10):
        super().__init__()
        self.k = k
    
    def select(self, datapack:Datapack) -> VideoData:
        if len(datapack.pickset) == 0:
            return datapack.pick(0)
        top_k = min(self.k, len(datapack.pickset))
        index = random.randint(0, top_k - 1)
        return datapack.pick(index)
    
    
    
class WeightedRandomSelector(Selector):
    """
    select a video randomly from datapack, weighted by their scores
    """
    
    def __init__(self):
        super().__init__()
    
    def select(self, datapack:Datapack) -> VideoData:
        if len(datapack.pickset) == 0:
            return datapack.pick(0)
        
        log_scores = np.array([v.score.total_score for v in datapack.pickset])
        log_scores -= np.max(log_scores) # for numerical stability if all values are large negative (e.g. when depth is huge)
        weights = np.exp(log_scores) # convert to normal scores
        total_weight = np.sum(weights)
        if total_weight == 0:
            index = random.randint(0, len(datapack.pickset) - 1)
            return datapack.pick(index)
        
        weights /= total_weight
        selected_index = random.choices(range(len(datapack.pickset)), weights=weights.tolist(), k=1)[0]
        
        vid = datapack.pick(selected_index)
        return vid
    
    
    
class WeightedRandomTopKSelector(Selector):
    """
    select a video randomly from the top K scored videos in datapack, weighted by their scores
    """
    
    def __init__(self, k:int=10):
        super().__init__()
        self.k = k
    
    def select(self, datapack:Datapack) -> VideoData:
        if len(datapack.pickset) == 0:
            return datapack.pick(0)
        
        top_k = min(self.k, len(datapack.pickset))
        top_videos = datapack.pickset[:top_k]
        
        log_scores = np.array([v.score.total_score for v in top_videos])
        log_scores -= np.max(log_scores) # for numerical stability if all values are large negative (e.g. when depth is huge)
        weights = np.exp(log_scores) # convert to normal scores
        total_weight = np.sum(weights)
        if total_weight == 0:
            index = random.randint(0, top_k - 1)
            return datapack.pick(index)
        
        weights /= total_weight
        selected_index = random.choices(range(top_k), weights=weights.tolist(), k=1)[0]
        
        vid = datapack.pick(selected_index)
        return vid