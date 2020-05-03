#!/usr/bin/env bash

exec "${PY_ENV}/bin/celery" \
  --app=opwen_email_client.webapp.tasks \
  beat \
  --loglevel="${LOKOLE_LOG_LEVEL}"
