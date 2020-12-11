from ..worker.reddit import job
from ..common.queue import REDDIT, enqueue

from . import stream


for comment in stream():
    enqueue(REDDIT, job, comment)
