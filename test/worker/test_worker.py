import os
import time

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from src import worker
from src.queue import REDDIT
from src.worker import ReplyWith

from .. import mock_with_name


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