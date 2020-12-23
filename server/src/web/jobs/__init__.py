import json
import logging
import os

from typing import Dict, cast
from uuid import uuid4

import boto3

QUEUE = boto3.resource("sqs").Queue(os.getenv("JOBS_QUEUE", ""))
TABLE = boto3.resource("dynamodb").Table(os.getenv("JOBS_TABLE", ""))


def handler(event: Dict[str, object], context: object) -> Dict[str, object]:
    """HTTP request handler for `/jobs`."""
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


def create_job(*, mapset: str, replay: str, title: str) -> str:
    """Create a new job, and return its ID."""
    job = str(uuid4())
    logging.info(f"Creating job {id}")
    data = {
        "mapset": mapset,
        "replay": replay,
        "skin": "CirclePeople",
        "fps": 60,
    }
    TABLE.put_item(Item={"id": job, "title": title, **data})  # type: ignore
    QUEUE.send_message(MessageBody=json.dumps({"id": job, **data}))
    return job
