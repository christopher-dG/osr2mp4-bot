import os

from typing import Dict, Tuple

from flask import Flask, request

from ..jobs import DiscordJob, RedditJob

JSON = Tuple[Dict[str, object], int]
app = Flask(__name__)


@app.route("/jobs/<id>", method="GET")
def get_job_urls(id: str) -> JSON:
    job = Job.get(id)
    if job:
        return job.urls, 200
    else:
        return {}, 404


@app.route("/jobs", method="POST")
def create_job() -> JSON:
    data = request.json
    trigger = data["trigger"]
    if trigger == "discord":
        job = DiscordJob.new(
            channel=data["channel"],
            message=data["message"],
            replay_url=data["replay_url"],
        )
    elif trigger == "reddit":
        job = RedditJob.new(comment_id=data["comment_id"])
    else:
        return {"error": "unknown trigger"}, 400
    return {"id": job.id if job else None}, 200


@app.route("/errors", method="POST")
def report_error() -> JSON:
    job = Job.get(request.json["id"])
    if not job:
        return {}, 404
    job.error(request.json)
    return {}, 204


@app.route("/queue", method="GET")
def handler() -> JSON:
    return {"queue": os.environ["JOBS_QUEUE"]}, 200
