import logging
import os
import time

from typing import Optional

from redis import Redis

JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "1800"))
PREFIX = "video"
PROGRESS = "progress"
REDIS = Redis(os.getenv("REDIS_HOST", "localhost"))


def get_video(key: str) -> Optional[str]:
    """Get the URL to a previously uploaded video of `key`."""
    _wait(key)
    val = REDIS.get(f"{PREFIX}:{key}")
    return val.decode() if val else None


def set_video(key: str, url: str) -> None:
    """Set the URL of `key` to `url`."""
    REDIS.set(f"{PREFIX}:{key}", url)
    set_video_progress(key, False)


def set_video_progress(key: str, status: bool) -> None:
    """Mark `key` as being currently or no longer in progress."""
    key = f"{PREFIX}:{PROGRESS}:{key}"
    if status:
        REDIS.set(key, "true", ex=JOB_TIMEOUT)
    else:
        REDIS.delete(key)


def _wait(key: str) -> None:
    """Wait until a progress marker for `key` no longer exists."""
    key = f"{PREFIX}:{PROGRESS}:{key}"
    if not REDIS.get(key):
        return
    logging.info("Waiting for in-progress video...")
    while REDIS.get(key):
        time.sleep(1)
