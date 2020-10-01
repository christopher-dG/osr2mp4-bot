import os

from pathlib import Path
from tempfile import mkstemp

import requests

from osr2mp4.osr2mp4 import Osr2mp4
from selenium.webdriver import FirefoxOptions, Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.expected_conditions import title_is
from selenium.webdriver.support.ui import WebDriverWait


DOWNLOADS = Path(os.environ["DOWNLOADS_DIR"])


def firefox():
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    options = FirefoxOptions()
    options.set_preference("browser.download.dir", DOWNLOADS.as_posix())
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/download;application/octet-stream")
    host = os.getenv("SELENIUM_HOST", "127.0.0.1")
    return Remote(
        f"http://{host}:4444/wd/hub",
        desired_capabilities=DesiredCapabilities.FIREFOX,
        options=options,
    )


def osu_login() -> None:
    expected_title = "dashboard | osu!"
    with firefox() as ff:
        ff.get("https://osu.ppy.sh")
        ff.find_element(By.CLASS_NAME, "js-user-login--menu").click()
        ff.find_element(By.NAME, "username").send_keys(os.environ["OSU_USERNAME"])
        ff.find_element(By.NAME, "password").send_keys(os.environ["OSU_PASSWORD"])
        ff.find_element(By.CLASS_NAME, "js-captcha--submit-button").click()
        wait = WebDriverWait(ff, 10)
        wait.until(title_is(expected_title))


def osu_download(id: int) -> Path:
    osu_login()
    # TODO: Better way to identify the new file.
    before = set(DOWNLOADS.iterdir())
    with firefox() as ff:
        ff.get(f"https://osu.ppy.sh/b/{id}")
        ff.find_element(By.CLASS_NAME, "js-beatmapset-download-link").click()
    after = set(DOWNLOADS.iterdir())
    new = list(after.difference(before))
    assert len(new) == 1
    return new[0]


def streamable_upload(video: Path, title: str) -> str:
    url = "https://api.streamable.com/upload"
    auth = (os.environ["STREAMABLE_USERNAME"], os.environ["STREAMABLE_PASSWORD"])
    with video.open("rb") as f:
        resp = requests.post(url, auth=auth, files={"file": (title, f)})
        shortcode = resp.json()["shortcode"]
    video.unlink()
    return f"https://streamable.com/{shortcode}"


def record(beatmap: Path, replay: Path) -> Path:
    _, output = mkstemp(suffix=".mp4")
    data = {
        "osu! path": "/",
        "Skin path": os.environ["OSU_SKIN_PATH"],
        "Beatmap path": beatmap.as_posix(),
        ".osr path": replay.as_posix(),
        "Default skin path": os.environ["OSU_SKIN_PATH"],
        "Output path": output,
        "Width": 1280,
        "Height": 720,
        "FPS": 60,
        "Start time": 0,
        "End time": -1,
        "Video codec": "XVID",
        "Process": 2,
        "ffmpeg path": "ffmpeg",
    }
    settings = {
        "Show scoreboard": False,
        "Song volume": 100,
        "Effect volume": 100,
        "Use FFmpeg video writer": True,
        "api key": "",
    }
    osr = Osr2mp4(data, settings)
    osr.startall()
    osr.joinall()
    return Path(output)
