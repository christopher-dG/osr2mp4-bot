import logging
import os

from typing import Dict, Tuple

import requests

from osrparse import parse_replay
from osrparse.replay import Replay

from . import create_job
from ... import ReplyWith, osu, s3


def handler(body: Dict[str, str]) -> None:
    channel = body["channel"]
    message = body["message"]
    try:
        replay_bytes, replay_parsed = download_replay(body["osr"])
        replay = s3.upload(replay_bytes)
        beatmap = osu.get_mapset(md5=replay_parsed.beatmap_hash)
        if not beatmap:
            raise ReplyWith("Sorry, I couldn't find the mapset.")
        job = create_job(
            beatmap=beatmap,
            replay=replay,
            source={"type": "discord", "channel": channel, "message": message},
        )
        raise ReplyWith(f"Created job `{job['id']}`.")
    except ReplyWith as e:
        reply(channel, message, e.msg)


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


def reply(channel: str, message: str, content: str) -> None:
    logging.info(f"{channel}/{message}: {content}")
    token = os.environ["DISCORD_TOKEN"]
    resp = requests.post(
        f"https://discord.com/api/v8/channels/{channel}/messages",
        headers={"Authorization": f"Bot {token}"},
        json={"content": content, "message_reference": {"message_id": str(message)}},
    )
    resp.raise_for_status()
