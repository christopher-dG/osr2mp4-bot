from typing import Any
import socketio
import logging

from src.worker.cache import is_render_active, set_render_id

fmt = "%(asctime)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt)

def on_connect() -> None:
    logging.info('o!rdr websocket connected.')


def on_disconnect() -> None:
    logging.error('o!rdr websocket disconnected.')


def on_render_done(data: Any) -> None:
    try:
        if (is_render_active(data['renderID'])):
            set_render_id(data['renderID'], data['videoUrl'])
            logging.info(f"Got video url from o!rdr ws for render {data['renderID']} - {data['videoUrl']}")
    except Exception as e:
        logging.exception(f"o!rdr websocket: error handling render finished - data: {data}")


def on_render_failed(data: Any) -> None:
    try:
        if (is_render_active(data['renderID'])):
            set_render_id(data['renderID'], 'failed')
            logging.info(f"render {data['renderID']} failed - {data['errorMessage']}")
    except Exception as e:
        logging.exception(f"o!rdr websocket: error handling render failed - data: {data}")


def main() -> None:
    sio = socketio.Client()
    sio.on('connect', on_connect)
    sio.on('disconnect', on_disconnect)
    sio.on('render_done_json', on_render_done)
    sio.on('render_failed_json', on_render_failed)
    sio.connect('https://ordr-ws.issou.best')
