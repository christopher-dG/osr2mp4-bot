from typing import cast

from praw.models import Comment


def is_osubot_comment(comment: Comment) -> bool:
    """Is this comment an osu!bot score post comment?"""
    return cast(bool, comment.is_root and comment.author.name == "osu-bot")
