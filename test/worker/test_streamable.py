import os
import time

from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import Mock, patch

import pytest
import requests

from src.worker import ReplyWith, streamable

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


@patch("logging.error")
@patch("logging.info")
def test_check_response(info, error):
    resp = Mock(headers={"Content-Type": "text/html"})
    with pytest.raises(ReplyWith):
        streamable._check_response(resp)
    error.assert_called_with("Streamable did not return JSON")
    resp.headers["Content-Type"] = "application/json"
    resp.ok = False
    resp.status_code = 403
    resp.text = "foo"
    with pytest.raises(ReplyWith):
        streamable._check_response(resp)
    error.assert_called_with("Streamable upload failed (403)")
    info.assert_called_with("foo")
    resp.ok = True
    resp.status_code = 200
    resp.json = lambda: {"shortcode": None}
    resp.text = "bar"
    with pytest.raises(ReplyWith):
        streamable._check_response(resp)
    error.assert_called_with("Streamable did not return shortcode")
    info.assert_called_with("bar")
    resp.json = lambda: {"shortcode": "abc"}
    assert streamable._check_response(resp) is None
