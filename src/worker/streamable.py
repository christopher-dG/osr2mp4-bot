import os

import requests

from pathlib import Path


def upload(video: Path, title: str) -> str:
    url = "https://api.streamable.com/upload"
    auth = (os.environ["STREAMABLE_USERNAME"], os.environ["STREAMABLE_PASSWORD"])
    with video.open("rb") as f:
        files = {"file": (title, f)}
        resp = requests.post(url, auth=auth, files=files)
    shortcode = resp.json()["shortcode"]
    video.unlink()
    return f"https://streamable.com/{shortcode}"
