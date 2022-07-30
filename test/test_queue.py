import os

from unittest.mock import Mock, patch

from src import queue

from . import mock_with_name

COMMENTS = [
    Mock(saved=False, body="", is_root=True, author=mock_with_name("osu-bot")),
    Mock(saved=False, body="foo u/osu-bot record bar"),
    Mock(saved=False, body="", is_root=False, author=mock_with_name("osu-bot")),
    Mock(saved=True, body="foo u/osu-bot record bar"),
    Mock(saved=False, body="", is_root=True, author=mock_with_name("not-osu-bot")),
    Mock(saved=False, body="", is_root=True, author=mock_with_name("not-osu-bot")),
    Mock(saved=False, body="foo u/not-osu-bot record bar"),
    Mock(saved=False, body="something else", auth=mock_with_name("someone-else")),
]
REDDIT_ENV = {
    "REDDIT_USERNAME": "osu-bot",
    "REDDIT_CLIENT_ID": "a",
    "REDDIT_CLIENT_SECRET": "b",
    "REDDIT_PASSWORD": "c",
    "REDDIT_USER_AGENT": "d",
}


@patch.dict(os.environ, REDDIT_ENV)
@patch("src.queue.REDDIT")
def test_stream(reddit):
    reddit.subreddit.return_value.stream.comments.return_value = COMMENTS
    assert list(queue._stream()) == COMMENTS[:2]
