from shutil import rmtree

import pytest

from src.worker import osu

from .. import has_osu_creds


@pytest.mark.skipif(not has_osu_creds(), reason="Needs osu! credentials")
def test_download_mapset_e2e():
    path = osu.download_mapset(53827)
    assert path.is_dir()
    print(path)
    mp3 = path / "01 Intro (Alive).mp3"
    assert mp3.is_file()
    rmtree(path)


@pytest.mark.skipif(not has_osu_creds(), reason="Needs osu! credentials")
def test_download_replay_e2e():
    path = osu.download_replay(2968679845)
    assert path.suffix == ".osr"
    assert path.stat().st_size == 15674
    path.unlink()
