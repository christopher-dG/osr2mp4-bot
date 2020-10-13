import logging

from traceback import print_exc

from .osu import download_beatmap, download_replay
from .reddit import failure, finished, parse_item, stream, success
from .recorder import record
from .streamable import upload


def process_item(item):
    logging.info(f"Processing post {item.submission.id}: {item.submission.title}")
    logging.info(f"Triggered by: /u/{item.author}")
    try:
        logging.info("Parsing...")
        beatmap, score, title = parse_item(item)
        logging.info(f"beatmap={beatmap}, score={score}")
        logging.info("Downloading beatmap...")
        beatmap_path = download_beatmap(beatmap)
        logging.info(f"Beatmap downloaded to {beatmap_path}")
        logging.info("Downloading replay...")
        replay_path = download_replay(score)
        logging.info(f"Replay downloaded to {replay_path}")
        logging.info("Recording...")
        video = record(beatmap_path, replay_path)
        logging.info(f"Video recorded to {video}")
        logging.info("Uploading...")
        url = upload(video, title)
        logging.info(f"Video uploaded to {url}")
        success(item, url)
    except Exception as e:
        logging.info("Something failed...")
        print_exc()
        failure(item, e)
    finally:
        finished(item)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
for item in stream():
    process_item(item)
