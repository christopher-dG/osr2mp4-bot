import os

from pathlib import Path
from tempfile import mkdtemp
from zipfile import ZipFile

from selenium.webdriver import FirefoxOptions, Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt

DOWNLOADS = Path(os.environ["DOWNLOADS_DIR"])


def _firefox() -> WebDriver:
    options = FirefoxOptions()
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/octet-stream; application/download",
    )
    host = os.getenv("SELENIUM_HOST", "127.0.0.1")
    return Remote(
        f"http://{host}:4444/wd/hub",
        desired_capabilities=DesiredCapabilities.FIREFOX,
        options=options,
    )


def _login() -> WebDriver:
    ff = _firefox()
    ff.get("https://osu.ppy.sh")
    ff.find_element(By.CLASS_NAME, "js-user-login--menu").click()
    ff.find_element(By.NAME, "username").send_keys(os.environ["OSU_USERNAME"])
    ff.find_element(By.NAME, "password").send_keys(os.environ["OSU_PASSWORD"])
    ff.find_element(By.CLASS_NAME, "js-captcha--submit-button").click()
    return ff


def _download(f):
    # TODO: Better way to identify the new file.
    def wrapped(id: int) -> Path:
        before = set(DOWNLOADS.iterdir())
        f(id)
        after = set(DOWNLOADS.iterdir())
        new = list(after.difference(before))
        assert len(new) == 1
        return new[0]

    return wrapped


@retry(stop=stop_after_attempt(3))
@_download
def _download_beatmap(beatmap: int) -> Path:
    with _login() as ff:
        ff.get(f"https://osu.ppy.sh/b/{beatmap}")
        WebDriverWait(ff, 10).until(
            presence_of_element_located((By.CLASS_NAME, "js-beatmapset-download-link"))
        ).click()


def download_beatmap(beatmap: int) -> Path:
    """Download and extract a beatmap."""
    osz = _download_beatmap(beatmap)
    path = mkdtemp()
    with ZipFile(osz) as f:
        f.extractall(path)
    return Path(path)


@retry(stop=stop_after_attempt(3))
@_download
def download_replay(score: int) -> Path:
    """Download a replay."""
    with _login() as ff:
        ff.get(f"https://osu.ppy.sh/scores/osu/{score}")
        WebDriverWait(ff, 10).until(
            presence_of_element_located((By.LINK_TEXT, "Download Replay"))
        ).click()
