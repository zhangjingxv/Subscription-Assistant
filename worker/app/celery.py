from .celery_app import celery_app

# Alias for Celery CLI compatibility (expects a variable named `celery`)
celery = celery_app

