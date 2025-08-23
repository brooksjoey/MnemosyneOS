src/jobs/celery_app.py
from celery import Celery
from ..utils.settings import settings
from .beat_schedule import CELERY_BEAT_SCHEDULE

app = Celery(
    "mnemo",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.jobs.tasks"],
)
app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=4,
    task_default_queue="ingest",
    task_routes={
        "tasks.reflect": {"queue": "reflect"},
        "tasks.compress": {"queue": "compress"},
        "tasks.rebuild": {"queue": "rebuild"},
    },
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    task_time_limit=120,
    beat_schedule=CELERY_BEAT_SCHEDULE,  # <— no RedBeat
)