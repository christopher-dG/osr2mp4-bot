from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch, ANY
import pytest
from src.worker import ReplyWith, ordr


@patch("src.worker.ordr.ORDR_API_KEY", "123")
@patch("src.worker.ordr.requests")
def test_submit_delete_replay(requests):
    replay = Mock(open=lambda x: 'replay binary', unlink=MagicMock(return_value=None))
    ordr.submit_replay(replay, skin = 5)
    requests.post.assert_called_once_with('https://apis.issou.best/ordr/renders', files={
        'replayFile': ('replay.osr', 'replay binary'),
        'username': (None, 'osu-bot'),
        'resolution': (None, '1280x720'),
        'skin': (None, 5),
        'verificationKey': (None, "123"),
    })
    ordr.delete_replay(replay)
    replay.unlink.assert_called_once()

@patch('src.worker.ordr.logging')
@patch("src.worker.ordr.get_render_id", side_effect=[None, 'failed', 'url'])
@patch("src.worker.ordr.set_video_progress")
@patch("src.worker.ordr.set_video")
@patch("src.worker.ordr.success")
@patch("src.worker.ordr.enqueue")
def test_wait_and_set_video_url(enqueue, success, set_video, set_video_progress, get_render_id, logging):
    score_id = 12345678
    render_id = 'render-id-123'
    comment = 'str comment'
    def reset_mock():
        enqueue.reset_mock()
        get_render_id.reset_mock()
        success.reset_mock()
        set_video_progress.reset_mock()
        set_video.reset_mock()
    # test no video url returned
    ordr.wait_and_set_video_url(score_id, render_id, comment)
    get_render_id.assert_called_once_with(render_id)
    enqueue.assert_called_with(ANY, score_id, render_id, comment, wait=timedelta(seconds=2))
    reset_mock()
    # test video failed to render
    ordr.wait_and_set_video_url(score_id, render_id, comment)
    get_render_id.assert_called_once_with(render_id)
    set_video_progress.assert_called_once_with(score_id, False)
    enqueue.assert_not_called()
    assert 'the video failed to render' in logging.warning.call_args[0][0]
    reset_mock()
    # test video render succeeded
    ordr.wait_and_set_video_url(score_id, render_id, comment)
    get_render_id.assert_called_once_with(render_id)
    set_video.assert_called_once_with(score_id, 'url')
    success.assert_called_once_with(comment, 'url')
    set_video_progress.assert_called_once_with(score_id, False)
    enqueue.assert_not_called()