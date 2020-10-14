# osr2mp4-bot

A Reddit bot that records and uploads videos of osu! replays.
See [/u/osu-bot](https://reddit.com/u/osu-bot).
This is just a thin wrapper around [osr2mp4](https://github.com/uyitroa/osr2mp4-core), all credit belongs there.

To use it, comment `/u/osu-bot record` on a score post.

### Dev Notes

Environment variables that need to be set in `.envrc`:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_PASSWORD`
- `REDDIT_USERNAME`
- `REDDIT_USER_AGENT`
- `OSU_API_KEY`
- `OSU_USERNAME`
- `OSU_PASSWORD`
- `OSU_SKIN_PATH` (automatic in Docker)
- `STREAMABLE_USERNAME`
- `STREAMABLE_PASSWORD`
- `REDIS_HOST`
- `REDIS_AUTH`

Running the server:

```sh
docker build -f server.Dockerfile -t osr2mp4-server .
docker run -d --name osr2mp4-server --restart=unless-stopped --env-file=.envrc osr2mp4-server
```

Running the worker (as many as you want):

```sh
docker build -f worker.Dockerfile -t osr2mp4-worker .
docker run -d --name osr2mp4-worker --restart=unless-stopped --env-file=.envrc osr2mp4-worker
```

Also make sure you have Redis running somewhere.
