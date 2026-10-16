"""Celery app + beat schedule.

Run the worker locally with:

    celery -A app.workers.celery_app worker -l info

And the scheduler in a separate process:

    celery -A app.workers.celery_app beat -l info

In production, run both as systemd units or extra services in
docker-compose; see DEPLOY.md.
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import settings


celery_app = Celery(
    "jaikalki_hrms",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.jobs"],
)

celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=10 * 60,
    worker_max_tasks_per_child=1000,
)


# Run the daily compliance digest every morning at 09:00 IST.
celery_app.conf.beat_schedule = {
    "compliance-digest": {
        "task": "app.workers.jobs.send_compliance_digest",
        "schedule": crontab(hour=9, minute=0),
    },
    "purge-expired-otps": {
        "task": "app.workers.jobs.purge_expired_otps",
        "schedule": crontab(hour=3, minute=15),
    },
    # Team alerts check every 10 minutes; times are set in Settings.
    "team-alerts": {
        "task": "app.workers.jobs.run_team_alerts",
        "schedule": crontab(minute="*/10"),
    },
}
