#!/usr/bin/env bash

"${PY_ENV}/bin/celery" \
  --app="opwen_email_server.services.tasks" \
  worker \
  --concurrency="${CELERY_WORKERS}" \
  --loglevel="${LOKOLE_LOG_LEVEL}"
