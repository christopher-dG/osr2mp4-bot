import logging
import os

from pathlib import Path

import requests

from requests import Response
from requests_toolbelt import MultipartEncoder

from . import ReplyWith


def upload(video: Path, title: str) -> str:
    url = "https://httpbin.org/post"
    auth = (os.environ["STREAMABLE_USERNAME"], os.environ["STREAMABLE_PASSWORD"])
    with video.open("rb") as f:
        data = MultipartEncoder({"file": (title, f)})
        headers = {"Content-Type": data.content_type}
        resp = requests.post(url, auth=auth, data=data, headers=headers)
    video.unlink()
    _check_response(resp)
    shortcode = resp.json()["shortcode"]
    return f"https://streamable.com/{shortcode}"


def _check_response(resp: Response) -> None:
    ct_ok = "application/json" in resp.headers["Content-Type"].lower()
    sc_ok = ct_ok and isinstance(resp.json().get("shortcode"), str)
    if not resp.ok or not ct_ok or not sc_ok:
        logging.error(f"Error from Streamable ({resp.status_code}):\n{resp.text}")
        raise ReplyWith("Sorry, something went wrong with the video upload.")
