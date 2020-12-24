import json
import os

from typing import Dict


def handler(event: Dict[str, object], context: object) -> Dict[str, object]:
    return {"statusCode": 200, "body": json.dumps({"queue": os.environ["JOBS_QUEUE"]})}
