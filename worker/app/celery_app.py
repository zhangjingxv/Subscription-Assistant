"""
Celery application configuration for AttentionSync worker
"""

import os
from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "attentionsync",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.content_tasks",
        "app.tasks.processing_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
)

# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    # Fetch content from all active sources every hour
    "fetch-all-sources": {
        "task": "app.tasks.content_tasks.fetch_all_sources",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Process unprocessed items every 15 minutes
    "process-pending-items": {
        "task": "app.tasks.processing_tasks.process_pending_items",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    
    # Generate daily digests at 6 AM
    "generate-daily-digests": {
        "task": "app.tasks.processing_tasks.generate_daily_digests",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM
    },
    
    # Cleanup old data weekly
    "cleanup-old-data": {
        "task": "app.tasks.processing_tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2:00 AM
    },
    
    # Health check every 5 minutes
    "health-check": {
        "task": "app.tasks.content_tasks.health_check",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    }
}

if __name__ == "__main__":
    celery_app.start()