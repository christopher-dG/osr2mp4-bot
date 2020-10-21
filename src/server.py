import os

from typing import Iterable

from praw import Reddit
from praw.models import Comment
from redis import Redis
from rq import Queue

from .worker import job
from .common import is_osubot_comment


REDDIT = Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
    user_agent=os.environ["REDDIT_USER_AGENT"],
)
QUEUE = Queue(
    connection=Redis(os.getenv("REDIS_HOST", "localhost")),
    default_timeout=int(os.getenv("JOB_TIMEOUT", "900")),
)


def _stream() -> Iterable[Comment]:
    for comment in REDDIT.subreddit("osugame").stream.comments():
        if comment.saved:
            continue
        if is_osubot_comment(comment):
            yield comment
        if f"u/{os.environ['REDDIT_USERNAME']} record" in comment.body:
            yield comment


def main() -> None:
    for comment in _stream():
        QUEUE.enqueue(job, comment)
