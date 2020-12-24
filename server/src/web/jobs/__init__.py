import json
import logging
import os

from typing import Dict, Optional, cast
from uuid import uuid4

import boto3

from ... import s3

QUEUE = boto3.resource("sqs").Queue(os.getenv("JOBS_QUEUE", ""))
TABLE = boto3.resource("dynamodb").Table(os.getenv("JOBS_TABLE", ""))


def handler(event: Dict[str, object], context: object) -> Dict[str, object]:
    """HTTP request handler for `/jobs`."""
    method = event["httpMethod"]
    if method == "GET":
        return handle_get(event)
    elif method == "POST":
        return handle_post(event)
    else:
        logging.warning(f"Unhandled method {method}")
        return {"statusCode": 405}


def handle_get(event: Dict[str, object]) -> Dict[str, object]:
    job = get_job(cast(str, cast(Dict[str, object], event["queryParameters"])["job"]))
    if not job:
        return {"statusCode": 404}
    return job_urls(job)


def handle_post(event: Dict[str, object]) -> Dict[str, object]:
    body = json.loads(cast(str, event["body"]))
    trigger = body["trigger"]
    try:
        if trigger == "discord":
            from . import discord
            discord.handler(body)
        elif trigger == "reddit":
            from . import reddit
            reddit.handler(body)
        else:
            raise ValueError(f"Unkown trigger: {trigger}")
    except Exception:
        logging.exception("Something went wrong...")
        code = 500
    else:
        code = 200
    return {"statusCode": code}


def get_job(job: str) -> Optional[Dict[str, object]]:
    """Get a job by ID."""
    resp = TABLE.get_item(Key={"id": job})
    if "Item" not in resp:
        return None
    return resp["Item"]


def create_job(
    *,
    beatmap: str,
    replay: str,
    source: Dict[str, str],
    title: str = "Temp",
    skin: str = "CirclePeople",
    fps: int = 60,
) -> Dict[str, object]:
    """Create a new job."""
    id = str(uuid4())
    job = {
        "id": id,
        "beatmap": beatmap,
        "replay": replay,
        "source": source,
        "title": title,
        "skin": skin,
        "fps": fps,
    }
    logging.info(f"Creating job {id}")
    TABLE.put_item(Item=job)
    QUEUE.send_message(MessageBody=json.dumps(job))
    return job


def job_urls(job: Dict[str, object]) -> Dict[str, object]:
    """Get download and upload URLs for a job."""
    return {
        "beatmap": s3.download_url(cast(str, job["beatmap"])),
        "replay": s3.download_url(cast(str, job["replay"])),
        "skin": s3.download_url(cast(str, job["skin"])),
        "upload": s3.upload_url(cast(str, job["id"])),
    }
