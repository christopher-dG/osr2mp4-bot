import logging
import os

from datetime import timedelta
from pathlib import Path

import boto3
import requests

from requests import Response

from . import ReplyWith
from ..common.queue import enqueue


def upload(video: Path, title: str) -> str:
    """Upload `video` to Streamable."""
    logging.info("Uploading...")
    # This technique comes from: https://github.com/adrielcafe/AndroidStreamable
    # We're not actually uploading the file ourselves,
    # just supplying a URL where it can find the video file.
    # It's assumed that `video` is available at $SERVER_ADDR.
    # Docker Compose handles this, provided that $SERVER_ADDR is publically accessible.
    # If $SERVER_ADDR cannot be accessed, setting $USE_S3_URLS to `true` will upload
    # the video to the S3 bucket $S3_BUCKET, and its public URL will be used.
    # BEWARE: S3 IS EXPENSIVE AND SHOULD ONLY BE USED WHEN ABSOLUTELY NECESSARY.
    auth = os.environ["STREAMABLE_USERNAME"], os.environ["STREAMABLE_PASSWORD"]
    s3 = os.getenv("USE_S3_URLS") == "true"
    if s3:
        source_url = _s3_upload(video)
    else:
        source_url = f"{os.environ['SERVER_ADDR']}/{video.name}"
    params = {"url": source_url, "title": title}
    resp = requests.get("https://api.streamable.com/import", auth=auth, params=params)
    _check_response(resp)
    shortcode = resp.json()["shortcode"]
    # Because the response comes before the upload is actually finished,
    # we can't delete the video file yet, although we need to eventually.
    # Create a new job that handles that at some point in the future.
    enqueue(_wait, shortcode, video, s3=s3)
    url = f"https://streamable.com/{shortcode}"
    logging.info(f"Video uploaded to {url}")
    return url


def _s3_upload(video: Path) -> str:
    """Upload `video` to S3 and return a public URL."""
    # It's assumed that credentials are set via environment variables.
    s3 = boto3.client("s3")
    bucket = os.environ["S3_BUCKET"]
    key = video.name
    with video.open("rb") as f:
        s3.put_object(ACL="public-read", Body=f, Bucket=bucket, Key=key)
    return f"https://{bucket}.s3.amazonaws.com/{key}"


def _check_response(resp: Response) -> None:
    """Verify that the `resp` to an upload request indicates success."""
    ex = ReplyWith("Sorry, uploading to Streamable failed.")
    if resp.headers["Content-Type"] != "application/json":
        logging.error("Streamable did not return JSON")
        raise ex
    if not resp.ok:
        logging.error(f"Streamable upload failed ({resp.status_code})")
        logging.info(resp.text)
        raise ex
    if not isinstance(resp.json().get("shortcode"), str):
        logging.error("Streamable did not return shortcode")
        logging.info(resp.text)
        raise ex


def _wait(shortcode: str, video: Path, s3: bool = False) -> None:
    """Wait for the video with `shortcode` to be uploaded, then delete `video`."""
    resp = requests.get(f"https://api.streamable.com/videos/{shortcode}")
    if not resp.ok:
        logging.warning("Retrieving video failed")
        return
    status = resp.json()["status"]
    if status in [0, 1]:
        # Still in progress, so run this function again in a while.
        # In the meantime, exit so that the worker gets freed up.
        enqueue(_wait, shortcode, video, s3=s3, wait=timedelta(seconds=5))
    elif status == 2:
        # Upload is finished, we can delete the local file now.
        video.unlink()
        if s3:
            _s3_delete(video.name)
    else:
        # If this happens too much, then we'll run out of disk space.
        logging.warning(f"Status {status} from Streamable ({shortcode} {video})")


def _s3_delete(key: str) -> None:
    """Delete an object with `key` from the S3 bucket."""
    s3 = boto3.client("s3")
    s3.delete_object(Bucket=os.environ["S3_BUCKET"], Key=key)
