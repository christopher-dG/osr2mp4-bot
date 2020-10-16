import os

from praw import Reddit
from redis import Redis
from rq import Queue

from .worker import job


REDDIT = Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
    user_agent=os.environ["REDDIT_USER_AGENT"],
)
QUEUE = Queue(connection=Redis(os.getenv("REDIS_HOST", "localhost")))


def _stream():
    for item in REDDIT.inbox.stream():
        if item.subject not in ("comment reply", "username mention"):
            continue
        comment = REDDIT.comment(item.id)
        if comment.saved:
            continue
        if f"u/{os.environ['REDDIT_USERNAME']} record" not in comment.body:
            continue
        yield item


def main():
    for item in _stream():
        QUEUE.enqueue(job, item, job_timeout=900)
