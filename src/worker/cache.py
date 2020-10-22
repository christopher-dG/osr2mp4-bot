import logging
import os
import time

from typing import Optional

from redis import Redis

JOB_TIMEOUT = int(os.getenv("JOB_TIMEOUT", "900"))
PREFIX = "video"
PROGRESS = "progress"
REDIS = Redis(os.getenv("REDIS_HOST", "localhost"))


def get_video(score: int) -> Optional[str]:
    _wait(f"{PREFIX}:{PROGRESS}:{score}")
    val = REDIS.get(f"{PREFIX}:{score}")
    return val.decode() if val else None


def set_video(score: int, url: str) -> None:
    REDIS.set(f"{PREFIX}:{score}", url)
    set_video_progress(score, False)


def set_video_progress(score: int, status: bool) -> None:
    key = f"{PREFIX}:{PROGRESS}:{score}"
    if status:
        REDIS.set(key, "true", ex=JOB_TIMEOUT)
    else:
        REDIS.delete(key)


def _wait(key: str) -> None:
    if not REDIS.get(key):
        return
    logging.info("Waiting for in-progress video...")
    while REDIS.get(key):
        time.sleep(1)
