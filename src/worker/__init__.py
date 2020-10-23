import logging

from praw.models import Comment

from ..common import is_osubot_comment


class ReplyWith(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


from .cache import get_video, set_video, set_video_progress  # noqa: E402
from .osu import download_mapset, download_replay  # noqa: E402
from .recorder import record  # noqa: E402
from .reddit import failure, finished, parse_comment, reply, success  # noqa: E402
from .streamable import upload  # noqa: E402


def job(comment: Comment) -> None:
    """Acquire required resources, then produce/upload a video."""
    fmt = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    sub = comment.submission
    logging.info(f"Processing comment {comment.id} on {sub.id}: {sub.title}")
    logging.info(f"Triggered by: /u/{comment.author}")
    try:
        mapset, score, title = parse_comment(comment)
        video_url = get_video(score)
        if video_url:
            logging.info(f"Found video in cache ({video_url})")
        else:
            set_video_progress(score, True)
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
            set_video(score, video_url)
        success(comment, video_url)
    except ReplyWith as e:
        if is_osubot_comment(comment):
            logging.warning(e.msg)
        else:
            reply(comment, e.msg)
    except Exception:
        logging.exception("Something failed...")
        failure(comment)
    finally:
        try:
            set_video_progress(score, False)
        except NameError:
            # If something failed in parse_comment, there's no score ID.
            pass
        finished(comment)
