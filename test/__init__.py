import os

from unittest.mock import Mock
from uuid import uuid4

import boto3


def mock_with_name(name):
    m = Mock()
    m.name = name
    return m


def is_docker():
    return os.path.isfile("/.dockerenv")


def has_osu_api_creds():
    return _has_env_vars("OSU_API_KEY")


def has_osu_web_creds():
    return _has_env_vars("OSU_USERNAME", "OSU_PASSWORD")


def has_reddit_creds():
    return _has_env_vars(
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "REDDIT_USER_AGENT",
    )


def has_streamable_creds():
    return _has_env_vars("STREAMABLE_USERNAME", "STREAMABLE_PASSWORD")


def has_test_video():
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        return False
    s3 = boto3.client("s3")
    try:
        s3.head_object(Bucket=bucket, Key="test.mp4")
        return True
    except Exception:
        return False


def has_s3_access():
    bucket = os.getenv("S3_BUCKET")
    if not bucket:
        return False
    s3 = boto3.client("s3")
    key = str(uuid4())
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=b"x")
        s3.get_object(Bucket=bucket, Key=key)
        s3.delete_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def _has_env_vars(*keys):
    return all(os.environ.get(k) for k in keys)


os.environ["REDDIT_USERNAME"] = "osu-bot"
