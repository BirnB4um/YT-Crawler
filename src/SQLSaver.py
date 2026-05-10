
import sqlite3

from VideoData import VideoData

class SQLSaver():

    def __init__(self, db_path:str):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()
    
    
    def _create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                channel TEXT,
                views INTEGER,
                length INTEGER,
                uploaded INTEGER
            )
            """
        )
        
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                idx INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id TEXT NOT NULL,
                child_id TEXT NOT NULL,
                UNIQUE (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES videos(video_id),
                FOREIGN KEY (child_id) REFERENCES videos(video_id)
            )
            """
        )
        
        self.conn.commit()
    
    
    def save_videos(self, parent:VideoData, videos:list[VideoData]):
        
        if len(videos) == 0:
            return
    
        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO videos (
                video_id, title, channel, views, length, uploaded
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, 
            [
                (
                    v.video_id,
                    v.title,
                    v.channel,
                    v.views,
                    v.length,
                    v.uploaded
                ) for v in videos
            ]
        )
        
        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO recommendations (parent_id, child_id)
            VALUES (?, ?)
            """, 
            [(parent.video_id, v.video_id) for v in videos]
        )
        self.conn.commit()
        
        
    def close(self):
        self.conn.close()