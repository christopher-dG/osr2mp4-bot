from __future__ import annotations

import json
import logging
import os

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

import boto3

from . import discord, reddit
from .. import ReplyWith, s3


@dataclass
class Job:
    id: UUID
    beatmap_hash: str
    replay_hash: str
    source: Dict[str, str]
    title: str = "Temp"
    skin: str = "CirclePeople"
    fps: int = 60

    _QUEUE = boto3.resource("sqs").Queue(os.environ["JOBS_QUEUE"])
    _TABLE = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])

    @staticmethod
    def new(**kwargs: str) -> Optional[Job]:
        trigger = kwargs["trigger"]
        if trigger == "discord":
            mod = discord
        elif trigger == "reddit":
            mod = reddit
        else:
            logging.warning(f"Unrecognized trigger '{trigger}'")
            return None
        try:
            job = mod.create_job(**kwargs)
        except ReplyWith as e:
            reply(kwargs, e.msg)
        if job:
            job.save()
            job.send()
        return job

    def reply(self, msg: str) -> None:
        reply(self.source, msg)

    @staticmethod
    def get(id: str) -> Optional[Job]:
        item = Job._TABLE.get_item(Key={"id": id}).get("Item")
        if not item:
            return None
        item["id"] = UUID(item)
        return Job(**parse_ddb_item(item))  # type: ignore

    @property
    def urls(self) -> Dict[str, object]:
        return {
            "beatmap": s3.download_url(self.beatmap_hash),
            "replay": s3.download_url(self.replay_hash),
            "skin": s3.download_url(f"osk/{self.skin}.osk"),
            "upload": s3.upload_url(str(self.id)),
        }

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": str(self.id),
            "beatmap_hash": self.beatmap_hash,
            "replay_hash": self.replay_hash,
            "source": self.source,
            "title": self.title,
            "skin": self.skin,
            "fps": self.fps,
        }

    def save(self) -> None:
        self._TABLE.put_item(Item=self.to_dict())

    def send(self) -> None:
        self._QUEUE.send_message(MessageBody=json.dumps(self.to_dict()))

    def error(self, data: Dict[str, object]) -> None:
        pass


def reply(source: Dict[str, str], msg: str) -> None:
    source = source.copy()
    trigger = source.pop("trigger")
    if trigger == "discord":
        mod = discord
    elif trigger == "reddit":
        mod = reddit
    else:
        logging.warning(f"Unrecognized trigger '{trigger}'")
        return
    mod.reply(msg, **source)


def parse_ddb_item(item: object) -> object:
    if isinstance(item, Decimal):
        return int(item)
    elif isinstance(item, list):
        return [parse_ddb_item(x) for x in item]
    elif isinstance(item, dict):
        return {k: parse_ddb_item(v) for k, v in item.items()}
    else:
        return item
