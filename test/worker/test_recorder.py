import os
import subprocess

from pathlib import Path
from unittest.mock import patch

import pytest

from src.worker import recorder

from .. import is_docker


@pytest.mark.skipif(not is_docker(), reason="Needs Dockerized environment")
@patch.dict(os.environ, {"OSU_API_KEY": ""})
def test_e2e():
    mapset = Path.home() / "testenv" / "mapset"
    replay = Path.home() / "testenv" / "replay.osr"
    video = recorder.record(mapset, replay)
    assert video.is_file()
    assert video.stat().st_size > 10_000_000
    assert video.parent.as_posix() == os.environ["VIDEO_DIR"]
    assert video.suffix == ".mp4"
    assert not mapset.exists()
    assert not replay.exists()
    args = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0",
        video.as_posix(),
    ]
    proc = subprocess.run(args, capture_output=True, check=True)
    assert proc.stdout.decode().strip() == "1920,1080"
    video.unlink()
