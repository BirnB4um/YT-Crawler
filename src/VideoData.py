from dataclasses import dataclass, field
from Score import Score

import copy


@dataclass
class VideoData():
    video_id: str
    title: str = None
    channel: str = None
    views: int = None 
    length: int = None # in seconds
    uploaded: int = None # timestamp in seconds
    
    # Additional data fields
    tree_depth: int = 0
    score: Score = field(default_factory=Score)
    embedding: any = None
    
    
    def reset_additional_data(self) -> None:
        """
        Reset additional data fields to default values.
        """
        self.tree_depth = 0
        self.score = Score()
        self.embedding = None
        
    
    def copy(self) -> "VideoData":
        """
        Create a deep copy of the VideoData instance.
        """
        return copy.deepcopy(self)
    
    
    def process(self, parent: "VideoData") -> None:
        """
        Process the video data based on its parent video data.
        """
        self.tree_depth = parent.tree_depth + 1
        
    
    def __str__(self) -> str:
        return f"VideoData(video_id={self.video_id}, title={self.title}, channel={self.channel}, views={self.views}, length={self.length}, uploaded={self.uploaded}, tree_depth={self.tree_depth}, score={self.score})"