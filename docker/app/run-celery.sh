#!/usr/bin/env bash

if [[ "${CELERY_QUEUE_NAMES}" = "all" ]]; then
  CELERY_QUEUE_NAMES="inbound,written,send,mailboxreceived,mailboxsent"
fi

"${PY_ENV}/bin/celery" \
  --app="opwen_email_server.integration.celery" \
  worker \
  --concurrency="${QUEUE_WORKERS}" \
  --loglevel="${LOKOLE_LOG_LEVEL}" \
  --queues="${CELERY_QUEUE_NAMES}"
