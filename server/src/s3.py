import logging
import os

from hashlib import md5

import boto3

from botocore.exceptions import ClientError

BUCKET = os.getenv("S3_BUCKET", "")
S3 = boto3.client("s3")


def exists(key: str) -> bool:
    """Check if an object with given `key` exists."""
    try:
        S3.head_object(Bucket=BUCKET, Key=key)
        return True
    except ClientError:
        return False


def upload(content: bytes) -> str:
    """Upload something public to S3 and return its URL."""
    key = md5(content).hexdigest()
    logging.info(f"Uploading to {key}...")
    S3.put_object(ACL="public-read", Bucket=BUCKET, Key=key, Body=content)
    return url(key)


def url(key: str) -> str:
    """Get a URL to an S3 object."""
    return f"https://{BUCKET}.s3.amazonaws.com/{key}"
