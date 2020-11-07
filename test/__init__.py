import os

from unittest.mock import Mock


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


def has_streamable_creds():
    return _has_env_vars("STREAMABLE_USERNAME", "STREAMABLE_PASSWORD")


def _has_env_vars(*keys):
    return all(os.environ.get(k) for k in keys)


os.environ["REDDIT_USERNAME"] = "osu-bot"
