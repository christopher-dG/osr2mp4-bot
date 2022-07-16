import logging
import os

from datetime import timedelta
from pathlib import Path
from typing import Callable
from praw.models import Comment

import requests

from src.common import enqueue
from src.worker.cache import set_video
from src.worker.reddit import success

ORDR_API_KEY = os.environ.get("ORDR_API_KEY", "")
fmt = "%(asctime)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)

def submit_replay(replayFile: Path, skin: int = 3) -> str:
    multipart_form_data = {
        'replayFile': ('replay.osr', replayFile.open('rb')),
        'username': (None, 'osu-bot'),
        'resolution': (None, '1920x1080'),
        'skin': (None, skin),
        'verificationKey': (None, ORDR_API_KEY),
    }
    resp = requests.post('https://ordr-api.issou.best/renders', files=multipart_form_data)
    resp_json = resp.json()
    return resp_json['renderID'] if 'renderID' in resp_json.keys() else None

def wait_and_set_video_url(score: int, renderId: str, comment: Comment) -> None:
    resp = requests.get(f"https://ordr-api.issou.best/renders?renderID={renderId}")
    try:
        resp_json = resp.json()
        render_result = resp_json['renders'][0]
        if render_result['videoUrl'] != 'None':
            video_url = render_result['videoUrl']
            logging.info(f"Got video url from o!rdr api - {video_url}")
            set_video(score, video_url)
            return success(comment, video_url)
            
        enqueue(wait_and_set_video_url, score, renderId, comment, wait=timedelta(seconds=5))
    except Exception as e:
        logging.warning(f"Retrieving video/setting comment failed: {e}")
        return
