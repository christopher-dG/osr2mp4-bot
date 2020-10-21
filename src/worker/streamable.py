import logging
import os

from pathlib import Path

import requests

from requests import Response

from . import ReplyWith

MAX_SIZE = 512 * 1024 * 1024


def upload(video: Path, title: str) -> str:
    if video.stat().st_size > MAX_SIZE:
        raise ReplyWith("Sorry, the video file is too large for me to upload.")
    url = "https://api.streamable.com/upload"
    auth = (os.environ["STREAMABLE_USERNAME"], os.environ["STREAMABLE_PASSWORD"])
    with video.open("rb") as f:
        files = {"file": (title, f)}
        resp = requests.post(url, auth=auth, files=files)
    _check_response(resp)
    shortcode = resp.json()["shortcode"]
    video.unlink()
    return f"https://streamable.com/{shortcode}"


def _check_response(resp: Response) -> None:
    ct_ok = "application/json" in resp.headers["Content-Type"].lower()
    sc_ok = ct_ok and isinstance(resp.json().get("shortcode"), str)
    if not resp.ok or not ct_ok or not sc_ok:
        logging.error(f"Error from Streamable ({resp.status_code}):\n{resp.text}")
        raise ReplyWith("Sorry, something went wrong with the video upload.")
