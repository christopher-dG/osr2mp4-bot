import logging
import os

from pathlib import Path
from tempfile import mkstemp
from typing import Dict, Tuple

import requests

from discord import Attachment
from discord.ext.commands import Bot, Context
from osrparse import parse_replay
from osrparse.replay import Replay

from ..worker import ReplyWith
from ..worker.discord import job
from ..worker.recorder import find_skin, list_skins
from ..common.discord import failure, reply
from ..common.queue import DISCORD, enqueue

BOT = Bot(command_prefix="~")


def main() -> None:
    fmt = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    BOT.run(os.environ["DISCORD_TOKEN"])


@BOT.command()  # type: ignore
async def osr2mp4(ctx: Context, *args: str) -> None:
    message = (ctx.channel.id, ctx.message.id)
    logging.info(f"Message: {message}")
    if not ctx.message.attachments:
        reply(message, "Expected an attached replay file.")
        return
    try:
        kwargs = _parse_args(args)
        path, osr = _download_replay(ctx.message.attachments[0])
    except ReplyWith as e:
        reply(message, e.msg)
    except Exception:
        failure(message)
    else:
        enqueue(DISCORD, job, message, path, kwargs)
        reply(message, f"Queued, your job ID is `{osr.replay_hash}`.")


def _parse_args(args: Tuple[str, ...]) -> Dict[str, object]:
    """Parse command arguments."""
    kwargs: Dict[str, object] = {}
    for arg in args:
        if "=" not in arg:
            raise ReplyWith(f"Invalid argument `{arg}`.")
        k, v = arg.split("=", 1)
        if k == "skin":
            kwargs["skin"] = _validate_skin(v)
        elif k == "fps":
            kwargs["fps"] = _validate_fps(v)
        else:
            raise ReplyWith(f"Unrecognized argument `{k}`.")
    return kwargs


def _validate_skin(skin: str) -> str:
    """Make sure that the skin the user wants to use exists."""
    if find_skin(skin):
        return skin
    available = ", ".join(f"`{d}`" for d in list_skins())
    raise ReplyWith(f"That skin is not available. Available skins are: {available}.")


def _validate_fps(fps: str) -> int:
    """Validate and parse an FPS argument."""
    if not fps.isnumeric():
        raise ReplyWith("Invalid value for `fps`.")
    n = int(fps)
    if n < 0:
        raise ReplyWith("Invalid value for `fps`.")
    return n


def _download_replay(attachment: Attachment) -> Tuple[Path, Replay]:
    """Download a reply file and parse it."""
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
