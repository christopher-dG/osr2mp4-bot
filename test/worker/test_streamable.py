import os
import time

from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch

import pytest
import requests

from src.worker import streamable

from .. import has_streamable_creds, is_docker


@pytest.mark.skipif(
    not is_docker() or not has_streamable_creds(),
    reason="Needs Dockerized environment and Streamable credentials",
)
@patch.dict(os.environ, {"SERVER_ADDR": "https://radiantmediaplayer.com/media"})
def test_e2e():
    video = Path(mkdtemp()) / "big-buck-bunny-360p.mp4"
    video.touch()
    title = "DELETE ME"
    url = streamable.upload(video, title)
    shortcode = url.split("/")[-1]
    resp = requests.get(f"https://api.streamable.com/videos/{shortcode}")
    json = resp.json()
    assert json["url"] == f"streamable.com/{shortcode}"
    assert json["title"] == title
    assert json["status"] == 1
    for i in range(35):
        time.sleep(1)
        if not video.is_file():
            break
    assert not video.is_file()
