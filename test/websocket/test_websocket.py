from unittest.mock import Mock, patch
import pytest
from src.websocket import ws


@patch("src.websocket.ws.set_render_id")
@patch("src.websocket.ws.is_render_active", side_effect = [False, True])
def test_on_render_failed(is_render_active, set_render_id):
    data = { 'renderID': 123, 'errorMessage': 'error' }
    ws.on_render_failed(data)
    is_render_active.assert_called_once_with(123)
    set_render_id.assert_not_called()
    ws.on_render_failed(data)
    is_render_active.assert_called_with(123)
    set_render_id.assert_called_once_with(123, 'failed')

@patch("src.websocket.ws.set_render_id")
@patch("src.websocket.ws.is_render_active", side_effect = [False, True])
def test_on_render_done(is_render_active, set_render_id):
    data = { 'renderID': 123, 'videoUrl': 'https://ko-fi.com/wiekus' }
    ws.on_render_done(data)
    is_render_active.assert_called_once_with(123)
    set_render_id.assert_not_called()
    ws.on_render_done(data)
    is_render_active.assert_called_with(123)
    set_render_id.assert_called_once_with(123, data['videoUrl'])