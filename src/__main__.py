from .osu import download_beatmap, download_replay
from .reddit import failure, finished, parse_item, stream, success
from .recorder import record
from .streamable import upload


for item in stream():
    try:
        beatmap, score, title = parse_item(item)
        beatmap_path = download_beatmap(beatmap)
        replay_path = download_replay(score)
        video = record(beatmap_path, replay_path)
        url = upload(video, title)
        success(item, url)
    except Exception as e:
        failure(item, e)
    finally:
        finished(item)
