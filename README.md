# osr2mp4-bot

A Reddit bot that records and uploads videos of osu! replays.
See [/u/osu-bot](https://reddit.com/u/osu-bot).
This is just a thin wrapper around [osr2mp4](https://github.com/uyitroa/osr2mp4-core), all credit belongs there.

Most of its work is done automatically, but you can also trigger it manually by commenting `/u/osu-bot record` on a score post.

### Dev Notes

Environment variables that need to be set in `.env`:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_PASSWORD`
- `REDDIT_USERNAME`
- `REDDIT_USER_AGENT`
- `OSU_API_KEY`
- `OSU_USERNAME`
- `OSU_PASSWORD`
- `STREAMABLE_USERNAME`
- `STREAMABLE_PASSWORD`
- `SERVER_ADDR`
- `DISCORD_TOKEN`

```sh
docker-compose build
docker-compose run -u root worker sh -c 'chown 1000 $SHARE_DIR'
docker-compose up -d --scale worker=4
```

### Idea: Crowdsourced workers

- Queue managers create jobs on a "server" queue, these jobs have credentials
- Required resources are downloaded and made pubically available on the server
- Create a new job on a "worker" queue, job arguments are resource URLs
- Workers have no credentials, they download resources and record videos.
- DB: Run a Redis replica that's read-only and publically accessible

- Workers get a presigned upload URL
- On file upload, server transfers file to Streamable (Lambda)


##### Server

The thing that's always running on an actual computer.

- Listens to Reddit posts
- Listens to Discord commands
- Makes an HTTP request to schedule a job

Credentials needed:

- Reddit (to poll posts/comments)
- Discord (to receive commands)

##### Leader

The things running in Lambda that have credentials but no computing power.

Triggered by server:

- Job details from Reddit or Discord
- Download beatmap/replay, put in a public S3 bucket
- Put job in SQS queue, contains:
  - Upload URL (presigned S3)
  - Beatmap/replay/skin URLs
  - Recording options

Triggered by workers:

- Error reports: respond on Reddit/Discord
- Successful video upload: Upload to Streamable and confirm via Reddit/Discord

Credentials needed:

- Reddit (to create/edit comments)
- Discord (to send messages)
- osu! to download beatmaps/replays
- Streamable to upload videos

##### Worker

The things with limited credentials but lots of firepower

- Receives jobs from the leader by polling SQS
- Jobs contain download URLs for resources
- Resources are downloaded, video is recorded, post-processing, etc.
- Final video file is uploaded to S3 with a presigned URL from the leader
- Errors are reported via HTTP (temp API key can be given in job info)

Credentials needed:

- AWS to poll SQS

##### Costs

- SQS: trivial
- DDB: trivial
- S3 storage: trivial
- S3 bandwidth: 9c/GB (this could end up being a lot)
