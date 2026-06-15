import os

from celery import Celery


celery_app = Celery(
    "sci_workshop_worker",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)


@celery_app.task(name="app.worker.health_check")
def health_check() -> str:
    return "worker-placeholder-ok"
