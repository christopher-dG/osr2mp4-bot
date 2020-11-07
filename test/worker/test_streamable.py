import os
import time

from datetime import timedelta
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


@patch("src.worker.streamable.enqueue")
@patch("src.worker.streamable._check_response")
@patch("src.worker.streamable.requests.get")
@patch.dict(
    os.environ,
    {"SERVER_ADDR": "a", "STREAMABLE_USERNAME": "u", "STREAMABLE_PASSWORD": "p"},
)
def test_upload(get, check_response, enqueue):
    get.return_value.json = lambda: {"shortcode": "abc"}
    video = Path("/videos/foo.mp4")
    assert streamable.upload(video, "TITLE") == "https://streamable.com/abc"
    get.assert_called_with(
        "https://api.streamable.com/import",
        auth=("u", "p"),
        params={"url": "a/foo.mp4", "title": "TITLE"},
    )
    enqueue.assert_called_with(streamable._wait, "abc", video)


@patch("src.worker.streamable.logging.error")
@patch("src.worker.streamable.logging.info")
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


@patch("src.worker.streamable.enqueue")
@patch("src.worker.streamable.requests.get")
@patch("src.worker.streamable.logging.warning")
def test_wait(warning, get, enqueue):
    get.return_value = Mock(ok=False)
    video = Mock(__str__=lambda self: "<video>")
    streamable._wait("a", video)
    get.assert_called_with("https://api.streamable.com/videos/a")
    warning.assert_called_with("Retrieving video failed")
    get.return_value.json.assert_not_called()
    enqueue.assert_not_called()
    video.unlink.assert_not_called()
    get.return_value.ok = True
    get.return_value.json.side_effect = [{"status": 1}, {"status": 2}, {"status": 3}]
    streamable._wait("b", video)
    enqueue.assert_called_with(streamable._wait, "b", video, wait=timedelta(seconds=30))
    video.unlink.assert_not_called()
    streamable._wait("c", video)
    video.unlink.assert_called_with()
    streamable._wait("d", video)
    warning.assert_called_with("Status 3 from Streamable (d <video>)")
