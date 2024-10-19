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


def submit_replay(score: int, mods: int) -> Optional[str]:
    multipart_form_data = {
        # "replayFile": ("replay.osr", replay_file.open("rb"))
    }

    skin = os.environ.get("ORDR_NOMOD_SKIN") # normal skin
    if mods & 2: # EZ mod
        skin = os.environ.get("ORDR_EZ_SKIN")
    elif mods & 64 or mods & 512: # DT or NC mods
        skin = os.environ.get("ORDR_DT_SKIN")

    config = {
        "replayScoreId": f"{score}",
        "username": "u/osu-bot",
        "resolution": "1280x720",
        "customSkin": "true",
        "skin": skin,
        "inGameBGDim": "90",
        "showHitCounter": "true",
        "showAimErrorMeter": "true",
        "showScoreboard": "true",
        "showStrainGraph": "true",
        "showSliderBreaks": "true",
        "useBeatmapColors": "false",
        "useSkinColors": "true",
        "verificationKey": f"{ORDR_API_KEY}",
    }

    resp = requests.post(
        os.environ.get("ORDR_RENDERS_URL"), files=multipart_form_data, data=config
    )
    resp_json = resp.json()

    render_info = f"renderID: {resp_json['renderID']} - errorCode: {resp_json['errorCode']} - message: {resp_json['message']}" if "errorCode" in resp_json.keys() else None
    render_id = str(resp_json["renderID"]) if "renderID" in resp_json.keys() else None
    return render_info, render_id


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
