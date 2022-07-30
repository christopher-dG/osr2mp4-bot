from datetime import timedelta
from unittest.mock import Mock, patch

from src import common

from . import mock_with_name


@patch("src.common.QUEUE")
def test_enqueue(queue):
    common.enqueue(print, 1)
    queue.enqueue.assert_called_with(print, 1)
    queue.enqueue_in.assert_not_called()
    common.enqueue(print, 2, wait=timedelta(seconds=30))
    queue.enqueue_in.assert_called_with(timedelta(seconds=30), print, 2)


def test_is_osubot_comment():
    comment = Mock(is_root=True, author=mock_with_name("osu-bot"))
    assert common.is_osubot_comment(comment)
    comment.is_root = False
    assert not common.is_osubot_comment(comment)
    comment.is_root = True
    comment.author.name = "not-osu-bot"
    assert not common.is_osubot_comment(comment)
