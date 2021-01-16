from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING, Tuple
from uuid import uuid4

import requests

from osrparse import parse_replay
from osrparse.replay import Replay

from .. import ReplyWith, osu, s3

if TYPE_CHECKING:
    from . import Job


def create_job(**kwargs: str) -> Job:
    replay_bytes, replay_parsed = download_replay(kwargs["replay_url"])
    replay_hash = s3.upload(replay_bytes)
    beatmap_hash = osu.get_mapset(md5=replay_parsed.beatmap_hash)
    if not beatmap_hash:
        raise ReplyWith("Sorry, I couldn't find the mapset.")
    return Job(
        id=uuid4(),
        source=kwargs,
        beatmap_hash=beatmap_hash,
        replay_hash=replay_hash,
    )


def reply(content: str, *, channel_id: str, message_id: str) -> None:
    logging.info(f"{channel_id}/{message_id}: {content}")
    token = os.environ["DISCORD_TOKEN"]
    resp = requests.post(
        f"https://discord.com/api/v8/channels/{channel_id}/messages",
        headers={"Authorization": f"Bot {token}"},
        json={"content": content, "message_reference": {"message_id": message_id}},
    )
    resp.raise_for_status()


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
