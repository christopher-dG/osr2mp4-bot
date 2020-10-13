from traceback import print_exc

from .osu import download_beatmap, download_replay
from .reddit import failure, finished, parse_item, stream, success
from .recorder import record
from .streamable import upload


def process_item(item):
    print(f"Processing post {item.submission.id}: {item.submission.title}")
    print(f"Triggered by: /u/{item.author}")
    try:
        print("Parsing...")
        beatmap, score, title = parse_item(item)
        print(f"beatmap={beatmap}, score={score}")
        print("Downloading beatmap...")
        beatmap_path = download_beatmap(beatmap)
        print(f"Beatmap downloaded to {beatmap_path}")
        print("Downloading replay...")
        replay_path = download_replay(score)
        print(f"Replay downloaded to {replay_path}")
        print("Recording...")
        video = record(beatmap_path, replay_path)
        print(f"Video recorded to {video}")
        print("Uploading...")
        url = upload(video, title)
        print(f"Video uploaded to {url}")
        success(item, url)
    except Exception as e:
        print("Something failed...")
        print_exc()
        failure(item, e)
    finally:
        finished(item)


for item in stream():
    process_item(item)
