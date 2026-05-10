import json

import numpy as np
import os
from tqdm import tqdm
import time
import sqlite3

import sys
sys.path.append("../../src")

from Models import *
from ScoreFunction import *
from Score import *
Models()

from Crawler import *




run_name = "test_4"

base_path = "../../crawl_results/"

conn = sqlite3.connect(os.path.join(base_path, run_name, "videos.db"))
cursor = conn.cursor()

cursor.execute("SELECT * FROM videos")
videos = cursor.fetchall()

cursor.execute("SELECT * FROM recommendations")
recommendations = cursor.fetchall()

conn.close()


score_function = SmallVideoScoreFunction()


all_videos = {}
for id, title, channel, views, length, uploaded in videos:
    all_videos[id] = {
        "title": title,
        "channel": channel,
        "views": views,
        "length": length,
        "uploaded": uploaded,
        "depth": 0,
        "total_score": 0
    }

root = recommendations[0][0]

child_lookup = {}
child_seen = set()
child_seen.add(root)

for parent_id, child_id in recommendations:
    if child_id in child_seen:
        continue
    child_seen.add(child_id)
    if parent_id not in child_lookup:
        child_lookup[parent_id] = []
    child_lookup[parent_id].append(child_id)

parents_lookup = {}
for parent, children in child_lookup.items():
    for child in children:
        parents_lookup[child] = parent


for id in all_videos.keys():
    video = VideoData(
        video_id=id,
        title=all_videos[id]["title"],
        channel=all_videos[id]["channel"],
        views=all_videos[id]["views"],
        length=all_videos[id]["length"],
        uploaded=all_videos[id]["uploaded"],
        tree_depth=0,
        score=Score()
    )

    score = score_function._score_absolute(video)
    all_videos[id]["total_score"] = score.total_score



def format_uploaded(timestamp):
    if timestamp == 0:
        return "Unknown published date"
    diff = int(time.time() - timestamp)
    if diff < 60:
        return f"{diff} seconds ago"
    elif diff < 3600:
        return f"{diff // 60} minutes ago"
    elif diff < 86400:
        return f"{diff // 3600} hours ago"
    elif diff < 604800:
        return f"{diff // 86400} days ago"
    elif diff < 2592000:
        return f"{diff // 604800} weeks ago"
    elif diff < 31536000:
        return f"{diff // 2592000} months ago"
    else:
        return f"{diff // 31536000} years ago"



video_data = []

def add_video(id):
    global video_data
    if id not in all_videos:
        return
    
    video_data.append({
        "idx": len(video_data),
        "id": id,
        "title": all_videos[id].get("title", "unknown"),
        "views": all_videos[id].get("views", -1),
        "length": all_videos[id].get("length", -1),	
        "channel": all_videos[id].get("channel", "unknown"),
        "uploaded_ts": all_videos[id].get("uploaded") or 0,
        "uploaded": format_uploaded(all_videos[id].get("uploaded") or 0),
        "total_score": all_videos[id].get("total_score", -1),
        "in_history": id in child_lookup,
    })
    
for parent_id, children in child_lookup.items():
    add_video(parent_id)
    for child_id in children:
        if child_id not in child_lookup:
            add_video(child_id)





with open("webpage_template.html", "r", encoding="utf-8") as f:
    webpage_template = f.read()


def create_youtube_gallery(all_videos, output_file="youtube_gallery.html"):

    # Inject video JSON data into the template
    video_json = json.dumps(all_videos)
    html_final = webpage_template.replace("%VIDEO_DATA%", video_json)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"Gallery saved to {output_file}")



create_youtube_gallery(video_data, output_file="youtube_gallery.html")