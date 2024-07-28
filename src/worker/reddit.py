import logging
import os
import re

from typing import List, Tuple, cast

from osuapi import OsuApi, OsuMod, ReqConnector
from praw.exceptions import RedditAPIException
from praw.models import Comment

from . import ReplyWith
from ..common import is_osubot_comment

from dotenv import load_dotenv
load_dotenv()

LINK_TEXT = "Video replay of this score"
OSU_API = OsuApi(os.environ.get("OSU_API_KEY", ""), connector=ReqConnector())
RE_BEATMAP = re.compile(r"osu\.ppy\.sh/b/(\d+)")
RE_PLAYER = re.compile(r"osu\.ppy\.sh/u/(\d+)")
RE_LENGTH = re.compile(r"([\d:]{2,5}:\d{2})")
RE_MODS = re.compile(r"osr2mp4-mods: \+([A-Z]+)")
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


def parse_comment(comment: Comment) -> Tuple[int, int, str]:
    """Try to extract `mapset`, `score`, `title` from the comment tree."""
    comment = _find_osubot_comment(comment)
    mapset, beatmap, player, mods = _parse_osubot_comment(comment.body)
    score = _score_id(beatmap, player, mods)
    title = comment.submission.title
    return mapset, score, title, mods


def success(comment: Comment, url: str) -> None:
    """Complete a successful job."""
    if not is_osubot_comment(comment):
        reply(comment, f"Here you go: {url}")
    _edit_osubot_comment(comment, url)


def reply(comment: Comment, msg: str) -> None:
    """Reply to a comment, ignoring errors if the comment has been deleted."""
    try:
        comment.reply(msg)
    except RedditAPIException as e:
        for item in e.items:
            if item.error_type == "DELETED_COMMENT":
                break
        else:
            raise


def failure(comment: Comment) -> None:
    """Complete a failed job."""
    if not is_osubot_comment(comment):
        reply(comment, "Sorry, something unexpected went wrong.")


def finished(comment: Comment) -> None:
    """Complete a job regardless of its success or failure."""
    comment.save()


def _find_osubot_comment(comment: Comment) -> Comment:
    """Try to find an osu!bot score post comment in the comment tree."""
    if is_osubot_comment(comment):
        return comment
    for comment in comment.submission.comments:
        if is_osubot_comment(comment):
            return comment
    raise ReplyWith("Sorry, I couldn't find a /u/osu-bot comment to use.")


def _parse_osubot_comment(body: str) -> Tuple[int, int, int, int]:
    """Try to extract `mapset`, `beatmap`, `player`, and `mods`."""
    lines = body.splitlines()
    beatmap = _parse_beatmap(lines)
    mapset = _get_mapset(beatmap)
    player = _parse_player(lines)
    mods = _parse_mods(lines)
    _check_not_unranked(lines)
    _check_standard(lines)
    return mapset, beatmap, player, mods


def _parse_beatmap(lines: List[str]) -> int:
    """Parse the beatmap ID."""
    # Beatmap ID is always on the first line, just like the mapset ID.
    match = re.search(RE_BEATMAP, lines[0])
    if not match:
        raise ReplyWith("Sorry, I couldn't find the beatmap.")
    return int(match[1])


def _get_mapset(beatmap: int) -> int:
    """Get the mapset ID of a beatmap."""
    beatmaps = OSU_API.get_beatmaps(beatmap_id=beatmap)
    if not beatmaps:
        raise ReplyWith("Sorry, I couldn't find the mapset.")
    mapset = beatmaps[0].beatmapset_id
    return cast(int, mapset)


def _parse_player(lines: List[str]) -> int:
    """Parse the player ID."""
    # The line with the player ID depends on whether or not the beatmap has mods.
    match = RE_PLAYER.search(" ".join(lines[9:11]))
    if not match:
        raise ReplyWith("Sorry, I couldn't find the player.")
    return int(match[1])


def _parse_mods(lines: List[str]) -> int:
    """Parse the mods."""
    match = RE_MODS.search("\n".join(lines))
    mods = match[1] if match else ""
    # If there are no mods, 0 means nomod.
    return sum(MODS[mods[i : i + 2]] for i in range(0, len(mods), 2))  # noqa: E203


def _check_not_unranked(lines: List[str]) -> None:
    """Check that the mapset is not unranked."""
    # For unranked beatmaps, ranked status goes on the second line.
    if "Unranked" in lines[1]:
        raise ReplyWith("Sorry, I can't record replays for unranked maps.")


def _check_standard(lines: List[str]) -> None:
    """Check that the game mode is osu!standard."""
    # The game mode is on the first line, unless the beatmap is unranked,
    # in which case the game mode is on the second line. Unranked maps are rejected
    # anyways, but check both lines to make sure we get the right error message,
    # not matter which order the checks run in.
    if "osu!standard" not in "".join(lines[:2]):
        raise ReplyWith("Sorry, I can only record osu!standard plays.")


def _score_id(beatmap: int, player: int, mods: int) -> int:
    """Find the score ID and ensure that the replay is available."""
    scores = OSU_API.get_scores(beatmap, username=player, mods=OsuMod(mods))
    if not scores:
        raise ReplyWith("Sorry, I couldn't find the replay.")
    score = scores[0]
    if not score.replay_available:
        raise ReplyWith("Sorry, the replay is not available for download.")
    logging.info(f"Found score id {score.score_id}")
    return cast(int, score.score_id)


def _edit_osubot_comment(comment: Comment, url: str) -> None:
    """Add `url` to the score post comment."""
    comment = _find_osubot_comment(comment)
    # If two jobs ran on the same score at once, then a video link may have been added
    # since this job started. The progress-tracking cache should prevent this,
    # but we're being safe anyways.
    comment.refresh()
    if LINK_TEXT in comment.body:
        if url not in comment.body:
            logging.info(f"Duplicate video should be deleted: {url}")
        return
    lines = comment.body.splitlines()
    lines.insert(0, f"# **[{LINK_TEXT}]({url})**\n")
    comment.edit("\n".join(lines))
