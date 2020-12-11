import logging
import os

from pathlib import Path
from tempfile import mkstemp
from typing import Tuple

import requests

from discord import Attachment
from discord.ext.commands import Bot, Context
from osrparse import parse_replay
from osrparse.replay import Replay

from ..worker import ReplyWith
from ..worker.discord import job
from ..common.discord import failure, reply
from ..common.queue import DISCORD, enqueue

BOT = Bot(command_prefix="~")


def main() -> None:
    fmt = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    BOT.run(os.environ["DISCORD_TOKEN"])


@BOT.command()  # type: ignore
async def osr2mp4(ctx: Context) -> None:
    message = (ctx.channel.id, ctx.message.id)
    logging.info(f"Message: {message}")
    if not ctx.message.attachments:
        reply(message, "Expected an attached replay file.")
        return
    try:
        path, osr = _download_replay(ctx.message.attachments[0])
    except ReplyWith as e:
        reply(message, e.msg)
    except Exception:
        failure(message)
    else:
        enqueue(DISCORD, job, message, path)
        reply(message, f"Queued, your job ID is `{osr.replay_hash}`.")


def _download_replay(attachment: Attachment) -> Tuple[Path, Replay]:
    if attachment.size > 10_000_000:
        raise ReplyWith("Replay file is over 10MB.")
    if not attachment.filename.endswith(".osr"):
        raise ReplyWith("Expected a `.osr` file.")
    resp = requests.get(attachment.url)
    if not resp.ok:
        raise ReplyWith("Downloading replay file failed.")
    try:
        osr = parse_replay(resp.content)
    except Exception:
        raise ReplyWith("Invalid replay file.")
    _, path = mkstemp(dir=os.environ["SHARE_DIR"], suffix=".osr")
    with open(path, "wb") as f:
        f.write(resp.content)
    return Path(path), osr
