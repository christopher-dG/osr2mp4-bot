import os

from typing import Dict

from praw import Reddit


REDDIT = Reddit(
    username=os.getenv("REDDIT_USERNAME", ""),
    password=os.getenv("REDDIT_PASSWORD", ""),
    user_agent=os.getenv("REDDIT_USER_AGENT", ""),
    client_id=os.getenv("REDDIT_CLIENT_ID", ""),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
)


def handler(body: Dict[str, object]) -> None:
    pass
