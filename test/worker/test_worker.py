import os
import time

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from src import worker
from src.reddit import REDDIT
from src.worker import ReplyWith

from .. import has_reddit_creds, is_docker, mock_with_name


@pytest.mark.skipif(
    not is_docker() or not has_reddit_creds(),
    reason="Needs Dockerized environment and Reddit credentials",
)
@patch("src.worker.success")
@patch("src.worker.failure")
@patch("src.worker.finished")
@patch("src.worker.logging.info")
@patch.dict(os.environ, {"USE_S3_URLS": "true"})
def test_job_e2e(info, finished, failure, success):
    comment = REDDIT.comment("gbhul89")
    comment.submission.title = "DELETE ME"
    worker.job(comment)
    ok = [False, False]
    for call in info.mock_calls:
        if not call.args:
            continue
        if "Video recorded to" in call.args[0]:
            video = Path(call.args[0].split()[-1])
            ok[0] = True
        if "Video uploaded to" in call.args[0]:
            shortcode = call.args[0].split("/")[-1]
            ok[1] = True
    if not all(ok):
        pytest.fail("Video was not uploaded")
    resp = requests.get(f"https://api.streamable.com/videos/{shortcode}")
    assert resp.ok and shortcode in resp.json()["url"]
    for i in range(35):
        time.sleep(1)
        if not video.is_file():
            break
    assert not video.is_file()


@patch("src.worker.parse_comment", side_effect=ReplyWith("oops"))
@patch("src.worker.get_video", side_effect=ValueError(1))
@patch("src.worker.finished")
@patch("src.worker.failure")
@patch("src.worker.success")
@patch("src.worker.set_video_progress")
@patch("src.worker.reply")
def test_job_errors(
    reply, set_video_progress, success, failure, finished, get_video, parse_comment
):
    comment = Mock(
        id="com",
        author=mock_with_name("author"),
        submission=Mock(id="sub", title="title"),
    )
    worker.job(comment)
    reply.assert_called_with(comment, "oops")
    finished.assert_called_with(comment)
    failure.assert_not_called()
    set_video_progress.assert_not_called()
    parse_comment.side_effect = None
    parse_comment.return_value = (1, 2, "title")
    worker.job(comment)
    set_video_progress.assert_called_with(2, False)
    failure.assert_called_with(comment)
