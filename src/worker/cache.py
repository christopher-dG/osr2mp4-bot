import logging
import os
import time

from typing import Optional, cast

from redis import Redis

JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "1800"))
PREFIX = "video"
PROGRESS = "progress"
REDIS = Redis(os.getenv("REDIS_HOST", "localhost"))


def get_video(score: int) -> Optional[str]:
    """Get the URL to a previously uploaded video of `score`."""
    _wait(score)
    val = cast(Optional[bytes], REDIS.get(f"{PREFIX}:{score}"))
    return val.decode() if val else None


def set_video(score: int, url: str) -> None:
    """Set the URL of `score` to `url`."""
    REDIS.set(f"{PREFIX}:{score}", url)
    set_video_progress(score, False)


def set_video_progress(score: int, status: bool) -> None:
    """Mark `score` as being currently or no longer in progress."""
    key = f"{PREFIX}:{PROGRESS}:{score}"
    if status:
        REDIS.set(key, "true", ex=JOB_TIMEOUT)
    else:
        REDIS.delete(key)


def _wait(score: int) -> None:
    """Wait until a progress marker for `score` no longer exists."""
    key = f"{PREFIX}:{PROGRESS}:{score}"
    if not REDIS.get(key):
        return
    logging.info("Waiting for in-progress video...")
    while REDIS.get(key):
        time.sleep(1)
