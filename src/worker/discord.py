from pathlib import Path
from typing import Tuple

from osrparse import parse_replay_file

from . import ReplyWith, before_job, main_job
from ..common import OSU_API
from ..common.discord import failure, reply


def job(message: Tuple[int, int], osr: Path) -> None:
    """Main job for Discord triggers."""
    before_job()
    reply(message, "Starting job.")
    try:
        mapset, key = _parse_osr(osr)
        title = key  # TODO
        url = main_job(mapset, osr, title, key)
        _success(message, url)
    except ReplyWith as e:
        reply(message, e.msg)
    except Exception:
        failure(message)


def _parse_osr(path: Path) -> Tuple[int, str]:
    osr = parse_replay_file(path)
    key = f"replay:{osr.replay_hash}"
    beatmaps = OSU_API.get_beatmaps(beatmap_hash=osr.beatmap_hash)
    if not beatmaps:
        raise ReplyWith("Sorry, I couldn't find the mapset.")
    beatmap = beatmaps[0]
    mapset = beatmap.beatmapset_id
    return mapset, key


def _success(message: Tuple[int, int], url: str) -> None:
    reply(message, f"Here you go: {url}")
