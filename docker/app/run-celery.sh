#!/usr/bin/env bash

"${PY_ENV}/bin/celery" \
  --app="opwen_email_server.integration.celery" \
  worker \
  --concurrency="${QUEUE_WORKERS}" \
  --loglevel="${LOKOLE_LOG_LEVEL}"
  --Q="${CELERY_QUEUE_NAMES}"
