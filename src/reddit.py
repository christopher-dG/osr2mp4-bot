import os
import re

from pathlib import Path
from typing import Tuple

from osuapi import OsuApi, OsuMod, ReqConnector
from praw import Reddit

from . import KnownFailure, osu

BOT = Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
    user_agent=os.environ["REDDIT_USER_AGENT"],
)
OSU_API = OsuApi(os.environ["OSU_API_KEY"], connector=ReqConnector())
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


def _should_process(item):
    if item.subject != "username mention":
        return False
    comment = BOT.comment(item.id)
    if comment.saved:
        return False
    return f"/u/{os.environ['REDDIT_USERNAME']} record" in comment.body


def _score_id(beatmap: int, player: int, mods: int) -> int:
    scores = OSU_API.get_scores(beatmap, username=player, mods=OsuMod(mods))
    if not scores:
        raise KnownFailure("Sorry, I couldn't find the replay.")
    return scores[0].score_id


def _get_replay(beatmap: int, player: int, mods: int) -> Path:
    score = _score_id(beatmap, player, mods)
    return osu.download_replay(score)


def _find_osubot_comment(item):
    for comment in item.submission.comments:
        if comment.author.name == "osu-bot":
            return comment
    raise KnownFailure("Sorry, I couldn't find a /u/osu-bot comment to use.")


def _parse_mods(mods: str) -> int:
    return sum(MODS[mods[i : i + 2]] for i in range(0, len(mods), 2))


def _parse_osubot_comment(body) -> Tuple[int, int, int]:
    if "osu!standard" not in body:
        raise KnownFailure("Sorry, I can only record osu!standard plays.")
    lines = body.splitlines()
    # Beatmap info is always the first line (if the beatmap was found).
    beatmap_info = lines[0]
    match = re.search(RE_BEATMAP, beatmap_info)
    if not match:
        raise KnownFailure("Sorry, I couldn't find the beatmap.")
    beatmap = int(match[1])
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
    return beatmap, player, mods


def success(item, url: str):
    item.reply(f"Here you go: {url}")


def failure(item, e: Exception):
    if isinstance(e, KnownFailure):
        msg = e.args[0]
    else:
        msg = "Sorry, something unexpected went wrong."
    item.reply(msg)


def finished(item):
    item.save()


def parse_item(item) -> Tuple[int, int, str]:
    comment = _find_osubot_comment(item)
    beatmap, player, mods = _parse_osubot_comment(comment.body)
    score = _score_id(beatmap, player, mods)
    title = item.submission.title
    return beatmap, score, title


def stream():
    for item in BOT.inbox.stream():
        if _should_process(item):
            yield item
