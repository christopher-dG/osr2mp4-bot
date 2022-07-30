import pytest

from src.worker import osu

from .. import has_osu_web_creds


@pytest.mark.skipif(not has_osu_web_creds(), reason="Needs osu!web credentials")
def test_download_replay_e2e():
    path = osu.download_replay(2968679845)
    assert path.suffix == ".osr"
    assert path.stat().st_size == 15674
    path.unlink()
