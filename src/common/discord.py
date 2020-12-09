import logging
import os

from typing import Tuple

import requests


def failure(message: Tuple[int, int]) -> None:
    logging.exception("Something failed...")
    reply(message, "Sorry, something unexpected went wrong.")


def reply(channel_message: Tuple[int, int], content: str) -> None:
    channel, message = channel_message
    logging.info(f"{channel}/{message}: {content}")
    token = os.environ["DISCORD_TOKEN"]
    resp = requests.post(
        f"https://discord.com/api/v8/channels/{channel}/messages",
        headers={"Authorization": f"Bot {token}"},
        json={"content": content, "message_reference": {"message_id": str(message)}},
    )
    resp.raise_for_status()
