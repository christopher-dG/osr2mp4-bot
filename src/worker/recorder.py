import logging
import os
import sys

from pathlib import Path
from shutil import rmtree
from tempfile import mkstemp
from typing import List, Optional

from osr2mp4.osr2mp4 import Osr2mp4

from . import ReplyWith


def record(mapset: Path, replay: Path, skin: str = "CirclePeople") -> Path:
    """Record `replay` on `mapset`, returning the path to the video file."""
    logging.info("Recording...")
    # $SHARE_DIR must be served at $SERVER_ADDR, so that Streamable can read the file.
    # It's taken care of in Docker Compose.
    _, output = mkstemp(dir=os.environ["SHARE_DIR"], suffix=".mp4")
    data = {
        "osu! path": "/",
        "Skin path": find_skin(skin),
        "Beatmap path": mapset.as_posix(),
        ".osr path": replay.as_posix(),
        "Default skin path": find_skin("Default"),
        "Output path": output,
        "Width": 1920,
        "Height": 1080,
        "FPS": 60,
        "Start time": 0,
        "End time": -1,
        "Video codec": "XVID",
        "Process": 2,
        "ffmpeg path": "ffmpeg",
    }
    settings = {
        "Global leaderboard": True,
        "Song volume": 100,
        "Effect volume": 100,
        "Enable PP counter": True,
        "Use FFmpeg video writer": True,
        "api key": os.environ["OSU_API_KEY"],
    }
    # This variable will generally only be set in Docker.
    hostname = os.getenv("HOSTNAME", "unknown")
    logs = os.path.join(os.environ["SHARE_DIR"], f"osr2mp4-{hostname}.log")
    # Stop the `Osr2mp4` constructor from replacing `sys.excepthook`.
    hook = sys.excepthook
    osr = Osr2mp4(data, settings, logtofile=True, logpath=logs)
    sys.excepthook = hook
    osr.startall()
    osr.joinall()
    osr.cleanup()
    rmtree(mapset)
    replay.unlink()
    logging.info(f"Video recorded to {output}")
    return Path(output)


def list_skins() -> List[str]:
    """List all available skins."""
    return os.listdir(os.environ["OSU_SKINS_DIR"])


def find_skin(name: str) -> Optional[str]:
    """Get the path to a skin."""
    path = os.path.join(os.environ["OSU_SKINS_DIR"], name)
    return path if os.path.isdir(path) else None
