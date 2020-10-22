import os

from datetime import timedelta
from typing import Callable, Optional, cast

from praw.models import Comment
from redis import Redis
from rq import Queue

QUEUE = Queue(
    connection=Redis(os.getenv("REDIS_HOST", "localhost")),
    default_timeout=int(os.getenv("JOB_TIMEOUT", "900")),
)


def enqueue(
    f: Callable[..., None], *args: object, wait: Optional[timedelta] = None
) -> None:
    if wait:
        QUEUE.enqueue_in(wait, f, *args)
    else:
        QUEUE.enqueue(f, *args)


def is_osubot_comment(comment: Comment) -> bool:
    return cast(bool, comment.is_root and comment.author.name == "osu-bot")
