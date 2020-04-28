#!/usr/bin/env bash

exec gunicorn \
  --workers="${WEBAPP_WORKERS}" \
  --log-level="${LOKOLE_LOG_LEVEL}" \
  --bind="0.0.0.0:${PORT}" \
  opwen_email_client.webapp:app
