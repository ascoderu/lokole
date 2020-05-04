#!/usr/bin/env bash

exec celery \
  --app=opwen_email_client.webapp.tasks \
  beat \
  --loglevel="${LOKOLE_LOG_LEVEL}"
