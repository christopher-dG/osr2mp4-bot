from __future__ import annotations

import json
import logging
import os

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

import boto3

from .discord import DiscordJob
from .reddit import RedditJob
from .. import ReplyWith, s3


@dataclass
class Job:
    id: UUID
    beatmap_hash: str
    replay_hash: str
    title: str = "Temp"
    skin: str = "CirclePeople"
    fps: int = 60

    _QUEUE = boto3.resource("sqs").Queue(os.environ["JOBS_QUEUE"])
    _TABLE = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])

    @classmethod
    def new(cls, **kwargs: object) -> Optional[Job]:
        try:
            job = cls.create(**kwargs)
        except ReplyWith as e:
            cls.reply(e.msg, **kwargs)
            return None
        else:
            job.save()
            job.send()
            return job

    @staticmethod
    def get(id: str) -> Optional[Job]:
        item = Job._TABLE.get_item(Key={"id": id}).get("Item")
        if not item:
            return None
        item["id"] = UUID(item)
        for k, v in item.items():
            if isinstance(v, Decimal):
                item[k] = int(v)
        type = item["source"]["type"]
        if type == "discord":
            cls = DiscordJob
        elif type == "reddit":
            cls = RedditJob
        else:
            logging.warning(f"Unknown job type {type}")
            return None
        return cls(**item)

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
