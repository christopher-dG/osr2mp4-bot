import os

import requests

from praw import Reddit
from praw.models import Comment


USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT = Reddit(
    username=USERNAME,
    password=os.getenv("REDDIT_PASSWORD", ""),
    user_agent=os.getenv("REDDIT_USER_AGENT", ""),
    client_id=os.getenv("REDDIT_CLIENT_ID", ""),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
)


def main() -> None:
    for comment in REDDIT.subreddit("osugame").stream.comments():
        if not should_process(comment):
            continue
        payload = {"trigger": "reddit", "comment": comment.id}
        resp = requests.post(os.environ["ENDPOINT"], json=payload)
        if not resp.ok:
            if should_reply(comment):
                comment.reply("Sorry, something is wrong with the server right now.")
            comment.save()


def should_process(comment: Comment) -> bool:
    if comment.saved:
        return False
    elif comment.is_root and comment.author.name == "osu-bot":
        return True
    elif f"u/{USERNAME} record" in comment.body:
        return True
    else:
        return False


def should_reply(comment: Comment) -> bool:
    return comment.author.name != "osu-bot"


if __name__ == "__main__":
    main()
