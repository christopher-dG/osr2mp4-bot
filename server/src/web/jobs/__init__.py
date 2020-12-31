import json
import logging
import os

from typing import Dict, Optional, cast
from uuid import uuid4

import boto3

from ... import s3

QUEUE = boto3.resource("sqs").Queue(os.getenv("JOBS_QUEUE", ""))
TABLE = boto3.resource("dynamodb").Table(os.getenv("JOBS_TABLE", ""))



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
