# TODO: Move these into test_reddit and add other tests for the main_job.

import os
import time

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from src.reddit import REDDIT
from src.worker import ReplyWith, reddit

from .. import has_reddit_creds, is_docker, mock_with_name


@pytest.mark.skipif(
    not is_docker() or not has_reddit_creds(),
    reason="Needs Dockerized environment and Reddit credentials",
)
@patch("src.worker.reddit._success")
@patch("src.worker.reddit._failure")
@patch("src.worker.reddit._finished")
@patch("src.worker.reddit.logging.info")
@patch.dict(os.environ, {"USE_S3_URLS": "true"})
def test_job_e2e(info, finished, failure, success):
    comment = REDDIT.comment("gbhul89")
    comment.submission.title = "DELETE ME"
    reddit.job(comment)
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


@patch("src.worker.reddit._parse_comment", side_effect=ReplyWith("oops"))
@patch("src.worker.get_video", side_effect=ValueError(1))
@patch("src.worker.reddit._finished")
@patch("src.worker.reddit._failure")
@patch("src.worker.reddit._success")
@patch("src.worker.reddit._reply")
@patch("src.worker.main_job")
def test_job_errors(
    main_job, reply, success, failure, finished, get_video, parse_comment
):
    comment = Mock(
        id="com",
        author=mock_with_name("author"),
        submission=Mock(id="sub", title="title"),
    )
    reddit.job(comment)
    reply.assert_called_with(comment, "oops")
    finished.assert_called_with(comment)
    failure.assert_not_called()
    main_job.assert_not_called()
    # TODO: Figure out these tests.
    # parse_comment.side_effect = None
    # parse_comment.return_value = (1, 2, "title")
    # reddit.job(comment)
    # main_job.assert_called_with(2, False)
    # failure.assert_called_with(comment)
