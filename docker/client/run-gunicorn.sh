#!/usr/bin/env bash

exec "${PY_ENV}/bin/gunicorn" \
  --workers="${WEBAPP_WORKERS}" \
  --log-level="${LOKOLE_LOG_LEVEL}" \
  --bind="0.0.0.0:${WEBAPP_PORT}" \
  opwen_email_client.webapp:app
