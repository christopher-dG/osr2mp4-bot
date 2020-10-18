import os
import re

from typing import List, Tuple, cast

from osuapi import OsuApi, OsuMod, ReqConnector
from praw.models import Comment

from . import ReplyWith

OSU_API = OsuApi(os.environ["OSU_API_KEY"], connector=ReqConnector())
RE_MAPSET = re.compile(r"osu\.ppy\.sh/d/(\d+)")
RE_BEATMAP = re.compile(r"osu\.ppy\.sh/b/(\d+)")
RE_PLAYER = re.compile(r"osu\.ppy\.sh/u/(\d+)")
RE_LENGTH = re.compile(r"([\d:]{2,5}:\d{2})")
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


def failure(item: Comment) -> None:
    item.reply("Sorry, something unexpected went wrong.")


def finished(item: Comment) -> None:
    item.save()


def _find_osubot_comment(item: Comment) -> Comment:
    for comment in item.submission.comments:
        if comment.author.name == "osu-bot":
            return comment
    raise ReplyWith("Sorry, I couldn't find a /u/osu-bot comment to use.")


def _parse_osubot_comment(body: str) -> Tuple[int, int, int, int]:
    lines = body.splitlines()
    mapset = _parse_mapset(lines)
    beatmap = _parse_beatmap(lines)
    player = _parse_player(lines)
    mods = _parse_mods(lines)
    _check_replay_already_recorded(lines)
    _check_unranked(lines)
    _check_standard(lines)
    _check_length(lines)
    return mapset, beatmap, player, mods


def _parse_mapset(lines: List[str]) -> int:
    match = RE_MAPSET.search(lines[0])
    if not match:
        raise ReplyWith("Sorry, I couldn't find the mapset.")
    return int(match[1])


def _parse_beatmap(lines: List[str]) -> int:
    match = re.search(RE_BEATMAP, lines[0])
    if not match:
        raise ReplyWith("Sorry, I couldn't find the beatmap.")
    return int(match[1])


def _parse_player(lines: List[str]) -> int:
    match = RE_PLAYER.search(" ".join(lines[9:11]))
    if not match:
        raise ReplyWith("Sorry, I couldn't find the player.")
    return int(match[1])


def _parse_mods(lines: List[str]) -> int:
    match = RE_MODS.search(lines[6])
    mods = match[1] if match else ""
    return sum(MODS[mods[i : i + 2]] for i in range(0, len(mods), 2))  # noqa: E203


def _check_replay_already_recorded(lines: List[str]) -> None:
    if "https://streamable.com" in " ".join(lines):
        raise ReplyWith(
            "This score has already been recorded, see the stickied comment."
        )


def _check_unranked(lines: List[str]) -> None:
    if "Unranked" in lines[1]:
        raise ReplyWith("Sorry, I can't record replays for unranked maps.")


def _check_standard(lines: List[str]) -> None:
    if "osu!standard" not in lines[0]:
        raise ReplyWith("Sorry, I can only record osu!standard plays.")


def _check_length(lines: List[str]) -> None:
    match = RE_LENGTH.findall(" ".join(lines[5:7]))
    if match:
        length = match[-1]
        if length.count(":") == 2 or int(length[:2]) >= 10:
            raise ReplyWith("Sorry, I can't record replays longer than 10 minutes.")


def _score_id(beatmap: int, player: int, mods: int) -> int:
    scores = OSU_API.get_scores(beatmap, username=player, mods=OsuMod(mods))
    if not scores:
        raise ReplyWith("Sorry, I couldn't find the replay.")
    score = scores[0]
    if not score.replay_available:
        raise ReplyWith("Sorry, the replay is not available for download.")
    return cast(int, score.score_id)


def _edit_osubot_comment(item: Comment, url: str) -> None:
    comment = _find_osubot_comment(item)
    lines = comment.body.splitlines()
    lines.insert(lines.index("***"), f"[Streamable replay]({url})\n")
    comment.edit("\n".join(lines))
