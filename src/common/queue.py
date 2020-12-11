import os

from datetime import timedelta
from typing import Callable, Optional

from redis import Redis
from rq import Queue


def _queue(name: str) -> Queue:
    return Queue(
        connection=Redis(os.getenv("REDIS_HOST", "localhost")),
        default_timeout=int(os.getenv("JOB_TIMEOUT", "1800")),
    )


DEFAULT = _queue("default")
DISCORD = _queue("discord")
REDDIT = _queue("reddit")


def enqueue(
    q: Queue,
    f: Callable[..., None],
    *args: object,
    wait: Optional[timedelta] = None,
    **kwargs: object,
) -> None:
    """Add a job to the queue to be executed immediately by default or after `wait`."""
    if wait:
        # This requires the worker(s) to have --with-scheduler.
        q.enqueue_in(wait, f, *args, **kwargs)
    else:
        q.enqueue(f, *args, **kwargs)
