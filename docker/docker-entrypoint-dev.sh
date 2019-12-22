#!/usr/bin/env bash

if [[ "${HOT_RELOAD}" != "True" ]]; then
  exec "$@"
fi

rootdir="$(readlink -f "$(dirname "$0")/..")"

exec "${PY_ENV}/bin/watchmedo" \
  auto-restart \
  --debug-force-polling \
  --directory="${rootdir}/opwen_email_server" \
  --pattern='*.py' \
  --recursive \
  -- "$@"
