#!/usr/bin/env bash

"${PY_ENV}/bin/flower" \
  --app="opwen_email_server.integration.celery" \
  --port="${PORT}" \
  --url_prefix="flower" \
  --basic_auth="${FLOWER_USERNAME}:${FLOWER_PASSWORD}"
