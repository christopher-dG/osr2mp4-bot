import os

from typing import Iterable

from praw import Reddit
from praw.models import Comment

from ..common import is_osubot_comment

REDDIT = Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
    username=os.environ.get("REDDIT_USERNAME", ""),
    password=os.environ.get("REDDIT_PASSWORD", ""),
    user_agent=os.environ.get("REDDIT_USER_AGENT", ""),
)


def stream() -> Iterable[Comment]:
    """Generator for comments that should be reacted to."""
    for comment in REDDIT.subreddit("osugame").stream.comments():
        if comment.saved:
            continue
        elif is_osubot_comment(comment):
            yield comment
        elif f"u/{os.environ['REDDIT_USERNAME']} record" in comment.body:
            yield comment
