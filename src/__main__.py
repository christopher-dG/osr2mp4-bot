import logging

from .osu import download_mapset, download_replay
from .reddit import failure, finished, parse_item, stream, success
from .recorder import record
from .streamable import upload


def process_item(item):
    logging.info(f"Processing post {item.submission.id}: {item.submission.title}")
    logging.info(f"Triggered by: /u/{item.author}")
    try:
        logging.info("Parsing...")
        mapset, score, title = parse_item(item)
        logging.info(f"mapset={mapset}, score={score}")
        logging.info("Downloading mapset...")
        mapset_path = download_mapset(mapset)
        logging.info(f"Beatmap downloaded to {mapset_path}")
        logging.info("Downloading replay...")
        replay_path = download_replay(score)
        logging.info(f"Replay downloaded to {replay_path}")
        logging.info("Recording...")
        video = record(mapset_path, replay_path)
        logging.info(f"Video recorded to {video}")
        logging.info("Uploading...")
        url = upload(video, title)
        logging.info(f"Video uploaded to {url}")
        success(item, url)
    except Exception as e:
        logging.exception("Something failed...")
        failure(item, e)
    finally:
        finished(item)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
for item in stream():
    process_item(item)
