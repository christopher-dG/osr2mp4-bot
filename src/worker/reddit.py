import os
import re

from typing import Tuple

from osuapi import OsuApi, OsuMod, ReqConnector
from praw.models import Comment

from . import KnownFailure

OSU_API = OsuApi(os.environ["OSU_API_KEY"], connector=ReqConnector())
RE_MAPSET = re.compile(r"osu\.ppy\.sh/d/(\d+)")
RE_BEATMAP = re.compile(r"osu\.ppy\.sh/b/(\d+)")
RE_PLAYER = re.compile(r"osu\.ppy\.sh/u/(\d+)")
RE_MODS = re.compile(r"\|\s+\+([A-Z]+)")
MODS = {
    "NF": 1 << 0,
    "EZ": 1 << 1,
    "TD": 1 << 2,
    "HD": 1 << 3,
    "HR": 1 << 4,
    "SD": 1 << 5,
    "DT": 1 << 6,
    "RX": 1 << 7,
    "HT": 1 << 8,
    "NC": 1 << 6 | 1 << 9,
    "FL": 1 << 10,
    "AT": 1 << 11,
    "SO": 1 << 12,
    "AP": 1 << 13,
    "PF": 1 << 5 | 1 << 14,
    "V2": 1 << 29,
}


def parse_item(item: Comment) -> Tuple[int, int, str]:
    comment = _find_osubot_comment(item)
    mapset, beatmap, player, mods = _parse_osubot_comment(comment.body)
    score = _score_id(beatmap, player, mods)
    title = item.submission.title
    return mapset, score, title


def success(item: Comment, url: str) -> None:
    item.reply(f"Here you go: {url}")
    _edit_osubot_comment(item, url)


def failure(item: Comment, e: Exception) -> None:
    if isinstance(e, KnownFailure):
        msg = e.args[0]
    else:
        msg = "Sorry, something unexpected went wrong."
    item.reply(msg)


def finished(item: Comment) -> None:
    item.save()


def _find_osubot_comment(item: Comment) -> Comment:
    for comment in item.submission.comments:
        if comment.author.name == "osu-bot":
            return comment
    raise KnownFailure("Sorry, I couldn't find a /u/osu-bot comment to use.")


def _parse_osubot_comment(body: str) -> Tuple[int, int, int, int]:
    # Bail if the replay has already been recorded.
    if "https://streamable.com" in body:
        raise KnownFailure(
            "This score has already been recorded, see the stickied comment."
        )
    lines = body.splitlines()
    # Beatmap info is always the first line (if the beatmap was found).
    beatmap_info = lines[0]
    match = re.search(RE_MAPSET, beatmap_info)
    if not match:
        raise KnownFailure("Sorry, I couldn't find the mapset.")
    mapset = int(match[1])
    match = re.search(RE_BEATMAP, beatmap_info)
    if not match:
        raise KnownFailure("Sorry, I couldn't find the beatmap.")
    beatmap = int(match[1])
    if "osu!standard" not in " ".join(lines[:2]):
        raise KnownFailure("Sorry, I can only record osu!standard plays.")
    # Player info line depends on if there was a mod line.
    player_info = " ".join(lines[9:11])
    match = re.search(RE_PLAYER, player_info)
    if not match:
        raise KnownFailure("Sorry, I couldn't find the player.")
    player = int(match[1])
    # Mods line might not exist, in that case it's nomod.
    mods_info = lines[6]
    match = re.search(RE_MODS, mods_info)
    mods = _parse_mods(match[1]) if match else 0
    return mapset, beatmap, player, mods


def _parse_mods(mods: str) -> int:
    return sum(MODS[mods[i : i + 2]] for i in range(0, len(mods), 2))


def _score_id(beatmap: int, player: int, mods: int) -> int:
    scores = OSU_API.get_scores(beatmap, username=player, mods=OsuMod(mods))
    if not scores:
        raise KnownFailure("Sorry, I couldn't find the replay.")
    score = scores[0]
    if not score.replay_available:
        raise KnownFailure("Sorry, the replay is not available for download.")
    return score.score_id


def _edit_osubot_comment(item: Comment, url: str) -> None:
    comment = _find_osubot_comment(item)
    lines = comment.body.splitlines()
    lines.insert(lines.index("***"), f"[Streamable replay]({url})\n")
    comment.edit("\n".join(lines))
