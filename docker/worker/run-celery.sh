#!/usr/bin/env sh

/venv/bin/celery \
  --app="opwen_email_server.services.tasks" \
  worker \
  --concurrency="${CELERY_WORKERS}" \
  --loglevel="${LOKOLE_LOG_LEVEL}"
