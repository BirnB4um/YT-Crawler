FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Berlin

RUN mkdir -p /opt/yt-crawler/crawl_results
RUN mkdir -p /opt/yt-crawler/scripts

WORKDIR /opt/yt-crawler
COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel pybind11
RUN python -m pip install --no-cache-dir -r requirements.txt

# copy code
COPY src /opt/yt-crawler/src
COPY scripts/download_model.py /opt/yt-crawler/scripts
COPY scripts/start_crawl.py /opt/yt-crawler/scripts

# download model
RUN python /opt/yt-crawler/scripts/download_model.py


COPY start.sh .
RUN chmod 755 start.sh

ENTRYPOINT ["./start.sh"]