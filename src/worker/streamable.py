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
    with _firefox() as ff:
        _login(ff)
        url = _upload(ff, video, title)
    enqueue(_wait, url, video)
    return url


def _firefox() -> WebDriver:
    host = os.getenv("SELENIUM_HOST", "127.0.0.1")
    ff = Remote(
        f"http://{host}:4444/wd/hub",
        desired_capabilities=DesiredCapabilities.FIREFOX,
    )
    return ff


def _login(ff: WebDriver) -> None:
    ff.get("https://streamable.com/login")
    username, password = ff.find_elements(By.CLASS_NAME, "form-control")
    username.send_keys(os.environ["STREAMABLE_USERNAME"])
    password.send_keys(os.environ["STREAMABLE_PASSWORD"])
    password.submit()
    wait = WebDriverWait(ff, 10)
    wait.until(title_contains("Dashboard"))


def _upload(ff: WebDriver, video: Path, title: str) -> str:
    source_url = f"{os.environ['SERVER_ADDR']}/{video.name}"
    url_input = ff.find_element(By.CLASS_NAME, "form-control")
    url_input.send_keys(source_url)
    url_input.submit()
    wait = WebDriverWait(ff, 10)
    wait.until(element_to_be_clickable((By.CLASS_NAME, "done-button"))).click()
    ff.find_element(By.CLASS_NAME, "edit-title-input").send_keys(title)
    time.sleep(3)  # Let the frontend react to the change.
    return cast(str, ff.find_element(By.ID, "video-url-input").text)


def _wait(url: str, video: Path) -> None:
    shortcode = url.split("/")[-1]
    resp = requests.get(f"https://api.streamable.com/videos/{shortcode}")
    status = resp.json()["status"]
    if status == 1:
        enqueue(_wait, url, video, wait=timedelta(seconds=30))
    elif status == 2:
        video.unlink()
    else:
        logging.warning(f"Status {status} from Streamable ({shortcode} {video})")
