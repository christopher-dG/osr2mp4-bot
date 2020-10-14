import logging

from praw.models import Comment


class KnownFailure(Exception):
    pass


from .osu import download_mapset, download_replay
from .recorder import record
from .reddit import failure, finished, parse_item, success
from .streamable import upload


def job(item: Comment) -> None:
    fmt = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    logging.info(f"Processing post {item.submission.id}: {item.submission.title}")
    logging.info(f"Triggered by: /u/{item.author}")
    try:
        mapset, score, title = parse_item(item)
        logging.info(f"mapset={mapset}, score={score}")
        logging.info("Downloading mapset...")
        mapset_path = download_mapset(mapset)
        logging.info(f"Beatmap downloaded to {mapset_path}")
        logging.info("Downloading replay...")
        replay_path = download_replay(score)
        logging.info(f"Replay downloaded to {replay_path}")
        logging.info("Recording...")
        video_path = record(mapset_path, replay_path)
        logging.info(f"Video recorded to {video_path}")
        logging.info("Uploading...")
        video_url = upload(video_path, title)
        logging.info(f"Video uploaded to {video_url}")
        success(item, video_url)
    except Exception as e:
        logging.exception("Something failed...")
        failure(item, e)
    finally:
        finished(item)