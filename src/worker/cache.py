import logging
import os

from typing import Optional

import boto3

VIDEOS = boto3.resource("dynamodb").Table(os.environ["VIDEOS_TABLE_NAME"])
PROGRESS = "progress"


def get_video(score: int) -> Optional[str]:
    """Get the URL to a previously uploaded video of `score`."""
    item = VIDEOS.get_item(Key={"id": score}).get("Item")
    if not item:
        return None
    if item.get(PROGRESS):
        # TOOD: Exit but jump back here in a little while.
        logging.info(f"Video for score {score} is in progress...")
        raise Exception("TODO")
    return item["url"]


def set_video(score: int, url: str) -> None:
    """Set the URL of `score` to `url`."""
    VIDEOS.put_item(Item={"id": score, "url": url})


def set_video_progress(score: int, status: bool) -> None:
    """Mark `score` as being currently or no longer in progress."""
    item = VIDEOS.get_item(Key={"id": score}).get("Item")
    if item:
        item[PROGRESS] = status
    else:
        item = {"id": score, PROGRESS: True}
    VIDEOS.put_item(Item=item)
