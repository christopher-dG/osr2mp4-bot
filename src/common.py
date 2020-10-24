import os

from datetime import timedelta
from typing import Callable, Optional, cast

from praw.models import Comment
from redis import Redis
from rq import Queue

QUEUE = Queue(
    connection=Redis(os.getenv("REDIS_HOST", "localhost")),
    default_timeout=int(os.getenv("JOB_TIMEOUT", "1800")),
)


def enqueue(
    f: Callable[..., None], *args: object, wait: Optional[timedelta] = None
) -> None:
    """Add a job to the queue to be executed immediately by default or after `wait`."""
    if wait:
        # This requires the worker(s) to have --with-scheduler.
        QUEUE.enqueue_in(wait, f, *args)
    else:
        QUEUE.enqueue(f, *args)


def is_osubot_comment(comment: Comment) -> bool:
    """Is this comment an osu!bot score post comment?"""
    return cast(bool, comment.is_root and comment.author.name == "osu-bot")
