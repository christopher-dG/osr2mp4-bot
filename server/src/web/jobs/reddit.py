import logging
import os
import re

from typing import Dict, List, Tuple

from praw import Reddit
from praw.exceptions import RedditAPIException
from praw.models import Comment

from . import create_job
from ... import ReplyWith, osu

LINK_TEXT = "Streamable replay"
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
REDDIT = Reddit(
    username=os.getenv("REDDIT_USERNAME", ""),
    password=os.getenv("REDDIT_PASSWORD", ""),
    user_agent=os.getenv("REDDIT_USER_AGENT", ""),
    client_id=os.getenv("REDDIT_CLIENT_ID", ""),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
)


def handler(body: Dict[str, object]) -> None:
    comment_id = body["comment"]
    comment = REDDIT.comment(comment_id)
    sub = comment.submission
    logging.info(f"Processing comment {comment.id} on {sub.id}: {sub.title}")
    logging.info(f"Triggered by: /u/{comment.author}")
    try:
        mapset, score, title = parse_comment(comment)
        beatmap = osu.get_mapset(mapset)
        replay = osu.get_replay(score)
        create_job(
            beatmap=beatmap,
            replay=replay,
            title=sub.title,
            source={"type": "reddit", "comment": comment_id},
        )
    except ReplyWith as e:
        if is_osubot_comment(comment):
            logging.warning(e.msg)
        else:
            reply(comment, e.msg)


def is_osubot_comment(comment: Comment) -> bool:
    """Check whether or not this comment is created by osu!bot."""
    return comment.is_root and comment.author.name == "osu-bot"


def parse_comment(comment: Comment) -> Tuple[int, int, str]:
    """Try to extract `mapset`, `score`, `title` from the comment tree."""
    comment = find_osubot_comment(comment)
    mapset, beatmap, player, mods = parse_osubot_comment(comment.body)
    score = score_id(beatmap, player, mods)
    title = comment.submission.title
    return mapset, score, title


def find_osubot_comment(comment: Comment) -> Comment:
    """Try to find an osu!bot score post comment in the comment tree."""
    if is_osubot_comment(comment):
        return comment
    for comment in comment.submission.comments:
        if is_osubot_comment(comment):
            return comment
    raise ReplyWith("Sorry, I couldn't find a /u/osu-bot comment to use.")


def parse_osubot_comment(body: str) -> Tuple[int, int, int, int]:
    """Try to extract `mapset`, `beatmap`, `player`, and `mods`."""
    lines = body.splitlines()
    beatmap = parse_beatmap(lines)
    mapset = get_mapset(beatmap)
    player = _parse_player(lines)
    mods = _parse_mods(lines)
    _check_not_unranked(lines)
    _check_standard(lines)
    return mapset, beatmap, player, mods


def parse_beatmap(lines: List[str]) -> int:
    """Parse the beatmap ID."""
    # Beatmap ID is always on the first line, just like the mapset ID.
    match = re.search(RE_BEATMAP, lines[0])
    if not match:
        raise ReplyWith("Sorry, I couldn't find the beatmap.")
    return int(match[1])


def get_mapset(beatmap: int) -> int:
    """Get the mapset ID of a beatmap."""
    mapset = osu.mapset_id(beatmap=beatmap)
    if mapset:
        return mapset
    raise ReplyWith("Sorry, I couldn't find the mapset.")


def parse_player(lines: List[str]) -> int:
    """Parse the player ID."""
    # The line with the player ID depends on whether or not the beatmap has mods.
    match = RE_PLAYER.search(" ".join(lines[9:11]))
    if not match:
        raise ReplyWith("Sorry, I couldn't find the player.")
    return int(match[1])


def parse_mods(lines: List[str]) -> int:
    """Parse the mods."""
    # This will only match if there's a second row in the beatmap stats.
    match = RE_MODS.search(lines[6])
    mods = match[1] if match else ""
    # If there are no mods, 0 means nomod.
    return sum(MODS[mods[i : i + 2]] for i in range(0, len(mods), 2))  # noqa: E203


def check_not_unranked(lines: List[str]) -> None:
    """Check that the mapset is not unranked."""
    # For unranked beatmaps, ranked status goes on the second line.
    if "Unranked" in lines[1]:
        raise ReplyWith("Sorry, I can't record replays for unranked maps.")


def check_standard(lines: List[str]) -> None:
    """Check that the game mode is osu!standard."""
    # The game mode is on the first line, unless the beatmap is unranked,
    # in which case the game mode is on the second line. Unranked maps are rejected
    # anyways, but check both lines to make sure we get the right error message,
    # not matter which order the checks run in.
    if "osu!standard" not in "".join(lines[:2]):
        raise ReplyWith("Sorry, I can only record osu!standard plays.")


def score_id(beatmap: int, player: int, mods: int) -> int:
    """Find the score ID and ensure that the replay is available."""
    score = osu.score_id(beatmap, player, mods)
    if score:
        return score
    raise ReplyWith("Sorry, the replay is not available for download.")


def reply(comment: Comment, msg: str) -> None:
    """Reply to a comment, ignoring errors if the comment has been deleted."""
    logging.info(msg)
    try:
        comment.reply(msg)
    except RedditAPIException as e:
        for item in e.items:
            if item.error_type == "DELETED_COMMENT":
                break
        else:
            raise
