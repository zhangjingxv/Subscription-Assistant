from datetime import datetime
from .celery_app import celery_app


@celery_app.task(name="tasks.ping")
def ping() -> str:
    return f"pong:{datetime.utcnow().isoformat()}"


@celery_app.task(name="tasks.add")
def add(x: int, y: int) -> int:
    return x + y

