import time

from unittest.mock import Mock, patch

import pytest

from src import worker
from src.queue import REDDIT
from src.worker import ReplyWith
from src.worker import cache
from src.worker.cache import get_render_id, is_render_active

from .. import has_reddit_creds, is_docker, mock_with_name


@pytest.fixture(autouse=True)
def before_each():
    cache.REDIS.flushall()
    cache.REDIS.flushdb()


@pytest.mark.skipif(
    not is_docker() or not has_reddit_creds(),
    reason="Needs Dockerized environment, reddit creds",
)
@patch("src.worker.logging.info")
@patch("src.worker.ordr.ORDR_API_KEY", "devmode_success")
def test_job_e2e(info):
    comment = REDDIT.comment("gbhul89")
    comment.submission.title = "DELETE ME"
    worker.job(comment)
    ok = [False, False]
    for call in info.mock_calls:
        if not call.args:
            continue
        if "Replay downloaded to" in call.args[0]:
            ok[0] = True
        if "Replay submitted to o!rdr" in call.args[0]:
            render_id = call.args[0].split("(")[1].split(")")[0]
            ok[1] = is_render_active(render_id) is True
    for i in range(60):
        time.sleep(1)
        if all(ok) and get_render_id(render_id):
            return
    pytest.fail("Video was not generated by ordr")


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
    set_video_progress.assert_not_called()
    failure.assert_called_with(comment)
