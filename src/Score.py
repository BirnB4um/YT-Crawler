
from dataclasses import dataclass
import numpy as np

MIN_SCORE = -1e3
MAX_SCORE = 0.0

@dataclass
class Score():
    """
    All scores are stored in log-space
    """
    
    # absolute scores
    view_score: float = MAX_SCORE
    length_score: float = MAX_SCORE
    language_score: float = MAX_SCORE
    title_score: float = MAX_SCORE

    # relativ scores    
    depth_score: float = MAX_SCORE
    same_channel_score: float = MAX_SCORE
    similar_title_score: float = MAX_SCORE
    
    
    @property
    def absolute_score(self) -> float:
        """
        score only based on this video in log-space
        """
        return max(MIN_SCORE, self.view_score + self.length_score + self.language_score + self.title_score)
    
    
    @property
    def localized_score(self) -> float:
        """
        score only based on local influcences (no tree depth) in log-space
        """
        return max(MIN_SCORE, self.view_score + self.length_score + self.language_score + self.title_score + self.same_channel_score + self.similar_title_score)
    
    
    @property
    def total_score(self) -> float:
        """
        total score in log-space
        """
        return max(MIN_SCORE, self.view_score + self.length_score + self.language_score + self.title_score +
                self.depth_score + self.same_channel_score + self.similar_title_score)
        
    @property
    def normal_score(self) -> float:
        """
        total score in normal space
        """
        return np.exp(self.total_score)
        
        
    def __str__(self):
        return (f"Score(view: {round(self.view_score, 3)}, len: {round(self.length_score, 3)}, "
                f"lang: {round(self.language_score, 3)}, title: {round(self.title_score, 3)}, "
                f"depth: {round(self.depth_score, 3)}, channel: {round(self.same_channel_score, 3)}, "
                f"sim_title: {round(self.similar_title_score, 3)}, total: {round(self.total_score, 3)})")
    
    