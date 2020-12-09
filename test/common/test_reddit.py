from unittest.mock import Mock

from src.common import reddit

from .. import mock_with_name


def test_is_osubot_comment():
    comment = Mock(is_root=True, author=mock_with_name("osu-bot"))
    assert reddit.is_osubot_comment(comment)
    comment.is_root = False
    assert not reddit.is_osubot_comment(comment)
    comment.is_root = True
    comment.author.name = "not-osu-bot"
    assert not reddit.is_osubot_comment(comment)
