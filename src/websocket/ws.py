from typing import Any
import socketio
import logging

from src.worker.cache import is_render_active, set_render_id

fmt = "%(asctime)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)

sio = socketio.Client(reconnection=True)

@sio.event
def connect() -> None:
    logging.info("o!rdr websocket connected.")

@sio.event
def disconnect() -> None:
    logging.error("o!rdr websocket disconnected.")

@sio.on("render_done_json")
def on_render_done(data: Any) -> None:
    try:
        if is_render_active(data["renderID"]):
            set_render_id(data["renderID"], data["videoUrl"])
            logging.info(f"Got video url (id:{data['renderID']}) - {data['videoUrl']}")
    except Exception:
        logging.exception(
            f"o!rdr websocket: error handling render finished - data: {data}"
        )

@sio.on("render_failed_json")
def on_render_failed(data: Any) -> None:
    try:
        if is_render_active(data["renderID"]):
            set_render_id(data["renderID"], "failed")
            logging.info(f"render {data['renderID']} failed - {data['errorMessage']}")
    except Exception:
        logging.exception(
            f"o!rdr websocket: error handling render failed - data: {data}"
        )

def main() -> None:
    sio.connect("https://apis.issou.best", socketio_path="/ordr/ws")
    sio.wait()
