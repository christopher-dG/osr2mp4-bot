import os

from io import BytesIO
from pathlib import Path
from tempfile import mkdtemp, mkstemp
from zipfile import ZipFile

from requests import Session

from . import ReplyWith


def download_mapset(mapset: int) -> Path:
    """Download and extract `mapset`, returning its path."""
    content = _download(f"https://osu.ppy.sh/beatmapsets/{mapset}")
    out = mkdtemp()
    with ZipFile(BytesIO(content)) as f:
        f.extractall(out)
    return Path(out)


def download_replay(score: int) -> Path:
    """Download the replay for `score`, returning its path."""
    content = _download(f"https://osu.ppy.sh/scores/osu/{score}")
    _, out = mkstemp(suffix=".osr")
    with open(out, "wb") as f:
        f.write(content)
    return Path(out)


def _download(url: str) -> bytes:
    """Download something from osu!web at `url`, returning the file contents."""
    with _login() as sess:
        resp = sess.get(f"{url}/download", headers={"Referer": url})
    if not resp.ok:
        raise ReplyWith("Sorry, a download failed.")
    return resp.content


def _login() -> Session:
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
