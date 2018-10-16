#!/usr/bin/env bash

"${PY_ENV}/bin/celery" \
  --app="opwen_email_server.services.tasks" \
  worker \
  --concurrency="${QUEUE_WORKERS}" \
  --loglevel="${LOKOLE_LOG_LEVEL}"
  --Q=${STORE_WRITTEN_QUEUE_NAME},${SEND_QUEUE_NAME},${STORE_INBOUND_QUEUE_NAME}
