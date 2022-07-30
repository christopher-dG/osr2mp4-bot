import logging

from praw.models import Comment

from ..common import is_osubot_comment


class ReplyWith(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


from .cache import get_video, set_active_render, set_video_progress  # noqa: E402
from .osu import download_replay  # noqa: E402
from .reddit import failure, finished, parse_comment, reply, success  # noqa: E402
from src.worker.ordr import delete_replay, wait_and_set_video_url, submit_replay


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
            success(comment, video_url)
        else:
            set_video_progress(score, True)
            logging.info("Downloading replay...")
            replay_path = download_replay(score)
            logging.info(f"Replay downloaded to {replay_path}")
            logging.info("Submitting Replay to o!rdr...")
            render_id = submit_replay(replay_path)
            set_active_render(render_id)
            logging.info(f"Replay submitted to o!rdr ({render_id}) - waiting for video url")
            wait_and_set_video_url(score, render_id, comment)
            delete_replay(replay_path)
    except ReplyWith as e:
        if is_osubot_comment(comment):
            logging.warning(e.msg)
        else:
            reply(comment, e.msg)
    except Exception:
        logging.exception("Something failed...")
        failure(comment)
    finally:
        finished(comment)
