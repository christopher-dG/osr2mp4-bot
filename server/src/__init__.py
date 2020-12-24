import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ReplyWith(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg
