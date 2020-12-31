from __future__ import annotations

import logging
import os

from typing import Optional, Tuple
from uuid import uuid4

import requests

from osrparse import parse_replay
from osrparse.replay import Replay

from . import Job
from .. import ReplyWith, osu, s3


class DiscordJob(Job):
    @staticmethod
    def create(channel: str, message: str, replay_url: str) -> Optional[DiscordJob]:
        replay_bytes, replay_parsed = DiscordJob.download_replay(replay_url)
        replay_hash = s3.upload(replay_bytes)
        beatmap_hash = osu.get_mapset(md5=replay_parsed.beatmap_hash)
        if not beatmap_hash:
            raise ReplyWith("Sorry, I couldn't find the mapset.")
        return DiscordJob(
            id=uuid4(),
            beatmap_hash=beatmap_hash,
            replay_hash=replay_hash,
            channel=channel,
            message=message,
        )

    @staticmethod
    def reply(channel: str, message: str, content: str) -> None:
        logging.info(f"{channel}/{message}: {content}")
        token = os.environ["DISCORD_TOKEN"]
        resp = requests.post(
            f"https://discord.com/api/v8/channels/{channel}/messages",
            headers={"Authorization": f"Bot {token}"},
            json={"content": content, "message_reference": {"message_id": message}},
        )
        resp.raise_for_status()

    @staticmethod
    def download_replay(url: str) -> Tuple[bytes, Replay]:
        """Download a reply file and parse it."""
        resp = requests.get(url)
        if not resp.ok:
            raise ReplyWith("Downloading replay file failed.")
        try:
            osr = parse_replay(resp.content)
        except Exception:
            raise ReplyWith("Invalid replay file.")
        return resp.content, osr
