from ..worker import job
from ..common import enqueue

from . import stream


for comment in stream():
    enqueue(job, comment)
