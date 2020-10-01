# osr2mp4-bot

process:

- Look up beatmap + player (use existing osu-bot comment for shortcut)
- download beatmap + replay
- produce video
- upload to streamable with S3 URL
- delete video from disk

environment variables:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_PASSWORD`
- `REDDIT_USERNAME`
- `REDDIT_USER_AGENT`
- `OSU_API_KEY`
- `OSU_USERNAME`
- `OSU_PASSWORD`
- `OSU_SKIN_PATH`
- `STREAMABLE_USERNAME`
- `STREAMABLE_PASSWORD`
- `DOWNLOADS_DIR`
