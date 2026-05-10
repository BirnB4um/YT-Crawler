
import json
import os
import sqlite3

run_name = "test_5"

base_path = "../../crawl_results/"

conn = sqlite3.connect(os.path.join(base_path, run_name, "videos.db"))
cursor = conn.cursor()

cursor.execute("SELECT * FROM videos")
videos = cursor.fetchall()

cursor.execute("SELECT * FROM recommendations")
recommendations = cursor.fetchall()

conn.close()


all_videos = {}
for id, title, channel, views, length, uploaded in videos:
    all_videos[id] = {
        "title": title,
        "channel": channel,
        "views": views,
        "length": length,
        "uploaded": uploaded,
        "depth": 0,
        "total_score": 0.0
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


def get_title(id):
    title = all_videos.get(id, {}).get("title", f"Video {id}").replace("\n", " ").replace("\r", " ").replace(";", " ")
    title = f"{'📌' if id in child_lookup else ' '}" + title
    return title

def get_line(id):
    path = []
    current_id = id
    while current_id in parents_lookup:
        path.append(current_id)
        current_id = parents_lookup[current_id]
    path.append(current_id)
    path.reverse()
    title = ';'.join([get_title(vid_id) for vid_id in path])
    return f"{title} 1"

folded = []
for id, vid in all_videos.items():
    folded.append(get_line(id))
    


with open("tree.folded", "w", encoding="utf-8") as f:
    for line in folded:
        f.write(line + "\n")
