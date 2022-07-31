import time

from unittest.mock import patch

import pytest

from src.worker import cache

from .. import is_docker


@pytest.fixture(autouse=True)
def before_each():
    cache.REDIS.flushall()
    cache.REDIS.flushdb()


@pytest.mark.skipif(not is_docker(), reason="Needs Redis server")
@patch("src.worker.cache.JOB_TIMEOUT", 1)
def test_e2e():
    assert cache.get_video(1) is None
    cache.set_video(1, "a")
    assert cache.get_video(1) == "a"
    cache.set_video_progress(2, True)
    now = time.time()
    assert cache.get_video(2) is None
    assert time.time() - now >= 1
    cache.set_video_progress(3, True)
    now = time.time()
    cache.set_video(3, "b")
    assert cache.get_video(3) == "b"
    assert time.time() - now < 0.5


@patch("src.worker.cache.REDIS")
@patch("src.worker.cache.JOB_TIMEOUT", 1)
def test_active_render(redis):
    cache.set_active_render(1)
    redis.set.assert_called_once_with("render:1", "true", ex=1)
    redis.get.side_effect = [None, False, "true"]
    res = cache.is_render_active(1)
    redis.get.assert_called_once_with("render:1")
    assert res is False
    res = cache.is_render_active(1)
    assert res is False
    res = cache.is_render_active(1)
    assert res is True
    assert redis.get.call_count == 3


@patch("src.worker.cache.REDIS")
@patch("src.worker.cache.JOB_TIMEOUT", 1)
def test_get_set_render_id(redis):
    url = "https://ko-fi.com/wiekus"
    cache.set_render_id(1, url)
    redis.set.assert_called_once_with("video:render:1", url, ex=1)
    redis.get.side_effect = [None, url.encode()]
    res = cache.get_render_id(1)
    redis.get.assert_called_once_with("video:render:1")
    assert res is None
    res = cache.get_render_id(1)
    assert res == url
    assert redis.get.call_count == 2


@patch("src.worker.cache.REDIS")
@patch("src.worker.cache._wait")
def test_get_video(wait, redis):
    redis.get.side_effect = [b"abc", None]
    assert cache.get_video(1) == "abc"
    redis.get.assert_called_with("video:1")
    assert cache.get_video(2) is None
    redis.get.assert_called_with("video:2")


@patch("src.worker.cache.REDIS")
@patch("src.worker.cache.set_video_progress")
def test_set_video(set_video_progress, redis):
    cache.set_video(1, "a")
    redis.set.assert_called_with("video:1", "a")
    set_video_progress.assert_called_with(1, False)


@patch("src.worker.cache.REDIS")
def test_set_video_progress(redis):
    cache.set_video_progress(1, True)
    redis.set.assert_called_with("video:progress:1", "true", ex=1800)
    redis.delete.assert_not_called()
    cache.set_video_progress(1, False)
    redis.delete.assert_called_with("video:progress:1")


@patch("src.worker.cache.REDIS")
@patch("src.worker.cache.logging.info")
@patch("src.worker.cache.time.sleep")
def test_wait(sleep, info, redis):
    redis.get.side_effect = [None, "a", "b", None]
    cache._wait(1)
    redis.get.assert_called_with("video:progress:1")
    info.assert_not_called()
    sleep.assert_not_called()
    cache._wait(2)
    info.assert_called_with("Waiting for in-progress video...")
    sleep.assert_called_with(1)
