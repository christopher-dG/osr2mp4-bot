import logging
import os
import time

from datetime import timedelta
from pathlib import Path
from typing import cast

import requests

from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.expected_conditions import (
    element_to_be_clickable,
    title_contains,
)
from selenium.webdriver.support.ui import WebDriverWait

from ..common import enqueue


def upload(video: Path, title: str) -> str:
    """Upload `video` called `title` to Streamable, returning the URL."""
    with _webdriver() as wd:
        _wd_login(wd)
        url = _wd_upload(wd, video, title)
    # Because `wd_upload` returns before the upload is actually finished,
    # we can't delete the video file yet, although we need to eventually.
    # Create a new job that handles that at some point in the future.
    enqueue(_wait, url, video)
    return url


def _webdriver() -> WebDriver:
    """Get a `WebDriver` instance."""
    # This assumes either Docker Compose or a local, pre-running Selenium server.
    host = os.getenv("SELENIUM_HOST", "127.0.0.1")
    wd = Remote(
        f"http://{host}:4444/wd/hub",
        desired_capabilities=DesiredCapabilities.FIREFOX,
    )
    return wd


def _wd_login(wd: WebDriver) -> None:
    """Log `wd` into Streamable."""
    wd.get("https://streamable.com/login")
    username, password = wd.find_elements(By.CLASS_NAME, "form-control")
    username.send_keys(os.environ["STREAMABLE_USERNAME"])
    password.send_keys(os.environ["STREAMABLE_PASSWORD"])
    password.submit()
    wait = WebDriverWait(wd, 10)
    wait.until(title_contains("Dashboard"))


def _wd_upload(wd: WebDriver, video: Path, title: str) -> str:
    """Start the upload of `video` via `wd`."""
    # We're not actually uploading the file ourselves,
    # just supplying a URL where it can find the video file.
    # It's assumed that `video` is available at $SERVER_ADDR.
    # Docker Compose handles this, provided that $SERVER_ADDR is publically accessible.
    source_url = f"{os.environ['SERVER_ADDR']}/{video.name}"
    url_input = wd.find_element(By.CLASS_NAME, "form-control")
    url_input.send_keys(source_url)
    url_input.submit()
    wait = WebDriverWait(wd, 10)
    wait.until(element_to_be_clickable((By.CLASS_NAME, "done-button"))).click()
    wd.find_element(By.CLASS_NAME, "edit-title-input").send_keys(title)
    # Let the frontend react to the change.
    time.sleep(3)
    return cast(str, wd.find_element(By.ID, "video-url-input").text)


def _wait(url: str, video: Path) -> None:
    """Wait for the video at `url` to be uploaded, then delete the local `video`."""
    # Streamable's URL format is `streamable.com/<shortcode>`.
    shortcode = url.split("/")[-1]
    resp = requests.get(f"https://api.streamable.com/videos/{shortcode}")
    status = resp.json()["status"]
    if status == 1:
        # Still in progress, so run this function again in a while.
        # In the meantime, exit so that the worker gets freed up.
        enqueue(_wait, url, video, wait=timedelta(seconds=30))
    elif status == 2:
        # Upload is finished, we can delete the local file now.
        video.unlink()
    else:
        # If this happens too much, then we'll run out of disk space.
        logging.warning(f"Status {status} from Streamable ({shortcode} {video})")
