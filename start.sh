#!/bin/bash
echo "starting..."

cd /opt/yt-crawler/src
/usr/local/bin/python /opt/yt-crawler/scripts/start_crawl.py

tail -f /dev/null