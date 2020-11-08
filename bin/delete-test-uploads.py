#!/usr/bin/env python

"""
Before running this script, make sure you have a Selenium container running:
docker run \
  --detach \
  --rm \
  --publish 4444:4444 \
  --volume /dev/shm:/dev/shm \
  selenium/standalone-firefox:3.141.59-20201010
"""

import os
import sys
import time

from selenium.webdriver import Remote
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


title = sys.argv[1] if len(sys.argv) > 1 else "DELETE ME"
print(f"Looking for videos with title '{title}'")
with Remote(
    "http://127.0.0.1:4444/wd/hub", desired_capabilities=DesiredCapabilities.FIREFOX
) as wd:
    wd.implicitly_wait(5)
    wd.get("https://streamable.com/login")
    username, password = wd.find_elements(By.CLASS_NAME, "form-control")
    username.send_keys(os.environ["STREAMABLE_USERNAME"])
    password.send_keys(os.environ["STREAMABLE_PASSWORD"])
    password.submit()
    wd.find_element(By.CLASS_NAME, "search-button").click()
    wd.find_element(By.CLASS_NAME, "filter-input").send_keys(title)
    time.sleep(3)
    count = 0
    for el in wd.find_elements(By.CLASS_NAME, "edit-title-input"):
        assert el.text == title
        count += 1
    if not count:
        print("There are no videos to delete")
        sys.exit()
    for el in wd.find_elements(By.CLASS_NAME, "rc-checkbox-input"):
        el.click()
    wd.find_element(By.PARTIAL_LINK_TEXT, "Delete Video").click()
    confirm = input(f"About to delete {count} video(s), continue? [yN] ")
    if confirm.lower().startswith("y"):
        wd.find_element(By.CLASS_NAME, "blue-button").click()
        print("Deleted")
    else:
        print("Aborted")
