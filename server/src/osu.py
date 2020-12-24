import logging
import os

from typing import Dict, Optional

from osuapi import OsuApi, OsuMod, ReqConnector
from requests import Session

from . import ReplyWith, s3

OSU_API = OsuApi(os.environ.get("OSU_API_KEY", ""), connector=ReqConnector())


def get_mapset(*, id: Optional[int] = None, md5: Optional[str] = None) -> Optional[str]:
    """Download `mapset` and return its S3 key."""
    if md5:
        logging.info(f"Downloading mapset by hash: {md5}")
        if s3.exists(md5):
            return md5
        else:
            id = mapset_id(md5=md5)
    if not id:
        logging.warning("No mapset ID")
        return None
    logging.info(f"Downloading mapset by ID: {id}")
    content = fetch(f"beatmapsets/{id}")
    return s3.upload(content)


def get_replay(score: int) -> str:
    """Download the replay for `score` and return its S3 key."""
    logging.info(f"Downloading replay {score}...")
    content = fetch(f"scores/osu/{score}")
    return s3.upload(content)


def score_id(beatmap: str, player: int, mods: int) -> Optional[int]:
    """Get the score ID for a play by `player` on `beatmap` with `mods`."""
    logging.info(f"Looking for score: beatmap={beatmap} player={player} mods={mods}")
    scores = OSU_API.get_scores(beatmap, username=player, mods=OsuMod(mods))
    if not scores:
        logging.warning("Couldn't find score")
        return None
    score = scores[0]
    if not score.replay_available:
        logging.warning("Replay is not available")
        return None
    return score.score_id


def mapset_id(
    *, beatmap: Optional[int] = None, md5: Optional[str] = None
) -> Optional[int]:
    """Get a mapset ID from its beatmap ID or hash."""
    if md5:
        kwargs: Dict[str, object] = {"beatmap_hash": md5}
    elif beatmap:
        kwargs = {"beatmap_id": beatmap}
    else:
        logging.warning("Neither beatmap nor md5 were supplied")
        return None
    beatmaps = OSU_API.get_beatmaps(**kwargs)
    return beatmaps[0].beatmapset_id if beatmaps else None


def fetch(url: str) -> bytes:
    """Download something from osu!web at `url`, returning the file contents."""
    url = f"https://osu.ppy.sh/{url}"
    with login() as sess:
        resp = sess.get(f"{url}/download", headers={"Referer": url})
    if not resp.ok:
        raise ReplyWith("Sorry, a download failed.")
    return resp.content


def login() -> Session:
    """Get a `Session` that's logged into osu!web."""
    # Technique comes from: https://github.com/TheBicPen/osu-lazer-bot.
    # There are also scripts out there that use `/session`,
    # but that seems to no longer work:
    # - https://github.com/iltrof/osumapd
    # - https://github.com/vincentmathis/osu-beatmap-downloader
    sess = Session()
    url = "https://osu.ppy.sh/forum/ucp.php?mode=login"
    data = {
        "username": os.environ["OSU_USERNAME"],
        "password": os.environ["OSU_PASSWORD"],
        "login": "Login",
    }
    resp = sess.post(url, data=data, headers={"Referer": url}, allow_redirects=False)
    if resp.status_code == 302:
        return sess
    raise ReplyWith("Sorry, I couldn't log into osu!web.")
