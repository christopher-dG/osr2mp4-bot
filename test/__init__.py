import os

from unittest.mock import Mock


def mock_with_name(name):
    m = Mock()
    m.name = name
    return m


def is_docker():
    return os.path.isfile("/.dockerenv")


def has_osu_creds():
    return "OSU_USERNAME" in os.environ and "OSU_PASSWORD" in os.environ


def has_streamable_creds():
    return "STREAMABLE_USERNAME" in os.environ and "STREAMABLE_PASSWORD" in os.environ


os.environ["OSU_API_KEY"] = "x"
os.environ["REDDIT_CLIENT_ID"] = "x"
os.environ["REDDIT_CLIENT_SECRET"] = "x"
os.environ["REDDIT_PASSWORD"] = "x"
os.environ["REDDIT_USER_AGENT"] = "x"

os.environ["REDDIT_USERNAME"] = "osu-bot"
