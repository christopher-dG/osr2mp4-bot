from datetime import timedelta
from unittest.mock import Mock

from src.common import queue


def test_enqueue():
    q = Mock()
    queue.enqueue(q, print, 1)
    q.enqueue.assert_called_with(print, 1)
    q.enqueue_in.assert_not_called()
    queue.enqueue(q, print, 2, wait=timedelta(seconds=30))
    q.enqueue_in.assert_called_with(timedelta(seconds=30), print, 2)
