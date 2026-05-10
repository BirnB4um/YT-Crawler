
from dataclasses import dataclass, field
from VideoData import VideoData
from Score import *

import random

@dataclass
class Datapack():
    
    top_k: int = 1_000 # max videos count in pickset
    trash_k: int = 10_000 # max videos count in trashset
    
    # Contains top_k videos with highest scores
    pickset: list[VideoData] = field(default_factory=list)
    
    # contains trash_k videos as backup
    trashset: list[VideoData] = field(default_factory=list)
    
    blacklist: set[str] = field(default_factory=set)
    
    
    def filter_blacklist(self, videos:list[VideoData]) -> list[VideoData]:
        return [vid for vid in videos if vid.video_id not in self.blacklist]
    
    
    def pick(self, idx:int=0) -> VideoData:
        """
        Pick a video from the pickset by index.  
        If out of range, pick randomly from trashset.  
        """
        if 0 <= idx < len(self.pickset):
            vid = self.pickset.pop(idx)
            return vid
        else:
            if not self.trashset:
                if not self.pickset:
                    raise IndexError("Trashset and Pickset are empty, cannot pick a video.")
                
                vid_idx = random.randint(0, len(self.pickset) - 1)
                vid = self.pickset.pop(vid_idx)
                return vid
            
            vid_idx = random.randint(0, len(self.trashset) - 1)
            vid = self.trashset.pop(vid_idx)
            return vid
            
        
    
    def add_videos(self, videos:list[VideoData]) -> None:
        """
        Add videos to the datapack.  
        Videos are added to pickset or trashset based on their scores.
        """
        combined = self.pickset + videos
        combined.sort(key=lambda v: v.score.total_score if v.score else MIN_SCORE, reverse=True)
        
        for v in videos:
            self.blacklist.add(v.video_id)
        
        self.pickset = combined[:self.top_k]
        
        self.trashset.extend(combined[self.top_k:])
        self.trashset = self.trashset[-self.trash_k:]
        
    
    def remove_video(self, video_id:str) -> bool:
        """
        Remove a video from pickset or trashset by video_id.  
        Returns True if removed, False if not found.
        """
        for vid_list in [self.pickset, self.trashset]:
            for i, vid in enumerate(vid_list):
                if vid.video_id == video_id:
                    vid_list.pop(i)
                    return True
        return False
        
    
    def squash(self, reset_after:bool=True) -> None:
        """
        Semi-reset the datapack.  
        Clears the trashset.
        keeps blacklist.
        Only keep top 100 videos in pickset.
        If reset_after is True, resets scores to 1.0 in remaining videos.
        """
        self.trashset = []
        self.pickset.sort(key=lambda v: v.score.total_score if v.score else MIN_SCORE, reverse=True)
        self.pickset = self.pickset[:100]
        
        if reset_after:
            for vid in self.pickset:
                # vid.reset_additional_data()
                vid.tree_depth = 0
                vid.score.depth_score = MAX_SCORE
                