import os
import sys

from pathlib import Path
from shutil import rmtree
from tempfile import gettempdir, mkstemp

from osr2mp4.osr2mp4 import Osr2mp4


def record(mapset: Path, replay: Path) -> Path:
    """Record `replay` on `mapset`, returning the path to the video file."""
    os.chdir(gettempdir())  # osr2mp4 tries to write to the working directory on error.
    _, output = mkstemp(dir=os.environ["FS_ROOT"], suffix=".mp4")
    data = {
        "osu! path": "/",
        "Skin path": os.environ["OSU_SKIN_PATH"],
        "Beatmap path": mapset.as_posix(),
        ".osr path": replay.as_posix(),
        "Default skin path": os.environ["OSU_SKIN_PATH"],
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
    # Stop the `Osr2mp4` constructor from replacing `sys.excepthook`.
    hook = sys.excepthook
    # TODO: Might want to log to /dev/null or an actual file.
    osr = Osr2mp4(data, settings)
    sys.excepthook = hook
    osr.startall()
    osr.joinall()
    osr.cleanup()
    rmtree(mapset)
    replay.unlink()
    return Path(output)
