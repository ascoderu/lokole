#!/usr/bin/env bash

if [[ "${CELERY_QUEUE_NAMES}" = "all" ]]; then
  CELERY_QUEUE_NAMES="$("${PY_ENV}/bin/python" -m opwen_email_server.integration.cli print-queues --separator=,)"
fi

"${PY_ENV}/bin/celery" \
  --app="opwen_email_server.integration.celery" \
  worker \
  --without-gossip \
  --without-heartbeat \
  --without-mingle \
  --concurrency="${QUEUE_WORKERS}" \
  --loglevel="${LOKOLE_LOG_LEVEL}" \
  --queues="${CELERY_QUEUE_NAMES}"
