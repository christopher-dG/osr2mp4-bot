from typing import cast

from praw.models import Comment


def is_osubot_comment(comment: Comment) -> bool:
    return cast(bool, comment.is_root and comment.author.name == "osu-bot")
