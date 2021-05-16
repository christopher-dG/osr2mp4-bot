import logging
import os

from pathlib import Path

import boto3
import requests

from requests import Response

from . import ReplyWith


def upload(video: Path, title: str) -> str:
    """Upload `video` to Streamable."""
    # This technique comes from: https://github.com/adrielcafe/AndroidStreamable
    # We're not actually uploading the file ourselves,
    # just supplying a URL where it can find the video file.
    auth = os.environ["STREAMABLE_USERNAME"], os.environ["STREAMABLE_PASSWORD"]
    source_url = _s3_upload(video)
    params = {"url": source_url, "title": title}
    resp = requests.get("https://api.streamable.com/import", auth=auth, params=params)
    _check_response(resp)
    shortcode = resp.json()["shortcode"]
    return f"https://streamable.com/{shortcode}"


def _s3_upload(video: Path) -> str:
    """Upload `video` to S3 and return a public URL."""
    s3 = boto3.client("s3")
    bucket = os.environ["S3_BUCKET"]
    key = f"mp4/{video.name}"  # Note: The `mp4/` prefix applies expiration.
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
