import os
import subprocess

from pathlib import Path
from unittest.mock import Mock, patch

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


@patch("src.worker.recorder.Osr2mp4")
@patch("src.worker.recorder.mkstemp", return_value=(1, "/videos/foo.mp4"))
@patch("src.worker.recorder.rmtree")
@patch.dict(
    os.environ,
    {
        "HOSTNAME": "me",
        "LOG_DIR": "/logs",
        "OSU_API_KEY": "abc",
        "OSU_SKIN_PATH": "/skin",
        "VIDEO_DIR": "/videos",
    },
)
def test_record(rmtree, mkstemp, osr2mp4):
    mapset = Path("a")
    replay = Mock(as_posix=lambda: "b")
    video = recorder.record(mapset, replay)
    assert video == Path("/videos/foo.mp4")
    rmtree.assert_called_with(mapset)
    replay.unlink.assert_called_with()
    call = osr2mp4.mock_calls[0]
    assert call.kwargs == {"logtofile": True, "logpath": "/logs/osr2mp4-me.log"}
    data, settings = call.args
    assert {
        ("Skin path", "/skin"),
        ("Default skin path", "/skin"),
        ("Beatmap path", "a"),
        (".osr path", "b"),
        ("Output path", "/videos/foo.mp4"),
    }.issubset(set(data.items()))
    assert settings["api key"] == "abc"
