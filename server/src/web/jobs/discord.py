import os

from typing import Dict

import requests

from osrparse import parse_replay
from osrparse.replay import Replay

from . import create_job
from ... import ReplyWith, osu


def handler(body: Dict[str, str]) -> None:
    try:
        replay_url = body["osr"]
        replay = download_replay(replay_url)
        mapset_url = osu.get_mapset(md5=replay.beatmap_hash)
        if not mapset_url:
            raise ReplyWith("Sorry, I couldn't find the mapset.")
        job = create_job(mapset=mapset_url, replay=replay_url, title="tmp")
        raise ReplyWith(f"Created job `{job}`.")
    except ReplyWith as e:
        reply(body["channel"], body["message"], e.msg)


def download_replay(url: str) -> Replay:
    """Download a reply file and parse it."""
    resp = requests.get(url)
    if not resp.ok:
        raise ReplyWith("Downloading replay file failed.")
    try:
        osr = parse_replay(resp.content)
    except Exception:
        raise ReplyWith("Invalid replay file.")
    return osr


def reply(channel: str, message: str, content: str) -> None:
    print(f"{channel}/{message}: {content}")
    token = os.environ["DISCORD_TOKEN"]
    resp = requests.post(
        f"https://discord.com/api/v8/channels/{channel}/messages",
        headers={"Authorization": f"Bot {token}"},
        json={"content": content, "message_reference": {"message_id": str(message)}},
    )
    resp.raise_for_status()
