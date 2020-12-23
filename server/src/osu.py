import logging
import os

from typing import Optional

from osuapi import OsuApi, ReqConnector
from requests import Session

from . import ReplyWith, s3

OSU_API = OsuApi(os.environ.get("OSU_API_KEY", ""), connector=ReqConnector())


def get_mapset(*, id: Optional[int] = None, md5: Optional[str] = None) -> Optional[str]:
    """Download `mapset`, returning its S3 URL."""
    if md5:
        logging.info(f"Downloading mapset by hash: {md5}")
        if s3.exists(md5):
            return s3.url(md5)
        else:
            id = mapset_id(md5)
    if not id:
        return None
    content = download(f"https://osu.ppy.sh/beatmapsets/{id}")
    return s3.upload(content)


def get_replay(score: int) -> str:
    """Download the replay for `score`, returning its path."""
    logging.info(f"Downloading replay {score}...")
    content = download(f"https://osu.ppy.sh/scores/osu/{score}")
    return s3.upload(content)


def mapset_id(md5: str) -> Optional[int]:
    """Get a mapset ID from its hash."""
    beatmaps = OSU_API.get_beatmaps(beatmap_hash=md5)
    return beatmaps[0].beatmapset_id if beatmaps else None


def download(url: str) -> bytes:
    """Download something from osu!web at `url`, returning the file contents."""
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
