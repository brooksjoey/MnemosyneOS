src/jobs/beat_schedule.py
from datetime import timedelta

CELERY_BEAT_SCHEDULE = {
  "reflect-hourly": {"task": "tasks.reflect", "schedule": timedelta(hours=1)},
  "compress-nightly": {"task": "tasks.compress", "schedule": timedelta(hours=24)},
}