import os
import sys

from pathlib import Path
from shutil import rmtree
from tempfile import mkstemp


def record(mapset: Path, replay: Path) -> Path:
    # This import is within the function so that the server can load this module
    # without having osr2mp4 available.
    from osr2mp4.osr2mp4 import Osr2mp4

    _, output = mkstemp(suffix=".mp4")
    data = {
        "osu! path": "/",
        "Skin path": os.environ["OSU_SKIN_PATH"],
        "Beatmap path": mapset.as_posix(),
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
        "Global leaderboard": True,
        "Song volume": 100,
        "Effect volume": 100,
        "Enable PP counter": True,
        "api key": os.environ["OSU_API_KEY"],
    }
    hook = sys.excepthook
    osr = Osr2mp4(data, settings)
    sys.excepthook = hook
    osr.startall()
    osr.joinall()
    osr.cleanup()
    rmtree(mapset)
    replay.unlink()
    return Path(output)
