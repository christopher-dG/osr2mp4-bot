import os

from unittest.mock import Mock

from dotenv import load_dotenv
load_dotenv()

def mock_with_name(name):
    m = Mock()
    m.name = name
    return m


def is_docker():
    return os.path.isfile("/.dockerenv")


def has_osu_api_creds():
    return _has_env_vars("OSU_API_KEY")


def has_osu_web_creds():
    return _has_env_vars("OSU_USERNAME", "OSU_PASSWORD")


def has_reddit_creds():
    return _has_env_vars(
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "REDDIT_USER_AGENT",
    )


def _has_env_vars(*keys):
    return all(os.environ.get(k) for k in keys)


os.environ["REDDIT_USERNAME"] = "osu-bot"
