import os

from io import BytesIO
from pathlib import Path
from tempfile import mkdtemp, mkstemp
from zipfile import ZipFile

from requests import Session

from . import KnownFailure


def _login() -> Session:
    # TODO: Reuse session until the cookie expires.
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
    raise KnownFailure("Sorry, I couldn't log into osu!web.")


def _download(url: str) -> bytes:
    with _login() as sess:
        resp = sess.get(f"{url}/download", headers={"Referer": url})
    if not resp.ok:
        raise KnownFailure("Sorry, a download failed.")
    return resp.content


def download_mapset(mapset: int) -> Path:
    content = _download(f"https://osu.ppy.sh/beatmapsets/{mapset}")
    out = mkdtemp()
    with ZipFile(BytesIO(content)) as f:
        f.extractall(out)
    return Path(out)


def download_replay(score: int) -> Path:
    content = _download(f"https://osu.ppy.sh/scores/osu/{score}")
    _, out = mkstemp(suffix=".osr")
    with open(out, "wb") as f:
        f.write(content)
    return Path(out)
