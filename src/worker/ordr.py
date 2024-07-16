import logging
import os

from datetime import timedelta
from pathlib import Path
from typing import Optional
from praw.models import Comment

import requests

from src.common import enqueue
from src.worker import ReplyWith
from src.worker.cache import get_render_id, set_video, set_video_progress
from src.worker.reddit import success

from dotenv import load_dotenv
load_dotenv()

ORDR_API_KEY = os.environ.get("ORDR_API_KEY", "")
fmt = "%(asctime)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)


def submit_replay(replay_file: Path, skin: int = 3) -> Optional[str]:
    multipart_form_data = {
        "replayFile": ("replay.osr", replay_file.open("rb")),
        "username": (None, "osu-bot"),
        "resolution": (None, "1280x720"),
        "skin": (None, skin),
        "verificationKey": (None, ORDR_API_KEY),
    }
    resp = requests.post(
        "https://apis.issou.best/ordr/renders", files=multipart_form_data
    )
    resp_json = resp.json()
    return str(resp_json["renderID"]) if "renderID" in resp_json.keys() else None


def delete_replay(replay_file: Path) -> None:
    replay_file.unlink(missing_ok=True)


def wait_and_set_video_url(score: int, render_id: str, comment: Comment) -> None:
    try:
        video_url = get_render_id(render_id)
        if video_url:
            logging.info(f"Got video url from o!rdr ws - {video_url}")

            if video_url == "failed":
                set_video_progress(score, False)
                raise ReplyWith("Sorry, the video failed to render.")

            set_video(score, video_url)
            success(comment, video_url)
            return set_video_progress(score, False)

        enqueue(
            wait_and_set_video_url, score, render_id, comment, wait=timedelta(seconds=2)
        )
    except Exception as e:
        logging.warning(f"waiting for video url failed: {e}")
