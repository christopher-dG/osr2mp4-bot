class ReplyWith(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg
