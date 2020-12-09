import os
from osuapi import OsuApi, ReqConnector


OSU_API = OsuApi(os.environ.get("OSU_API_KEY", ""), connector=ReqConnector())
