import logging

from pathlib import Path


class ReplyWith(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


from .cache import get_video, set_video, set_video_progress  # noqa: E402
from .osu import download_mapset  # noqa: E402
from .recorder import record  # noqa: E402
from .streamable import upload  # noqa: E402


def before_job() -> None:
    fmt = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)


def main_job(mapset: int, osr: Path, title: str, key: str) -> str:
    """Acquire required resources, then produce/upload a video."""
    logging.info(f"mapset={mapset}, osr={osr}, key={key}")
    url = get_video(key)
    if url:
        logging.info(f"Found video in cache ({url})")
        return url
    set_video_progress(key, True)
    try:
        mapset_path = download_mapset(mapset)
        video = record(mapset_path, osr)
        url = upload(video, title)
        set_video(key, url)
        return url
    except Exception as e:
        if not isinstance(e, ReplyWith):
            logging.exception("Something failed...")
        raise
    finally:
        set_video_progress(key, False)
