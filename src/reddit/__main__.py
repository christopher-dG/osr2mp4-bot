from ..worker.reddit import job
from ..common.queue import enqueue

from . import stream


for comment in stream():
    enqueue(job, comment)
