from datetime import timedelta
from unittest.mock import patch

from src.common import queue


@patch("src.common.queue.QUEUE")
def test_enqueue(q):
    queue.enqueue(print, 1)
    q.enqueue.assert_called_with(print, 1)
    q.enqueue_in.assert_not_called()
    queue.enqueue(print, 2, wait=timedelta(seconds=30))
    q.enqueue_in.assert_called_with(timedelta(seconds=30), print, 2)
