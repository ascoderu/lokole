#!/usr/bin/env bash

if [[ "${HOT_RELOAD}" != "True" ]]; then
  exec "$@"
fi

rootdir="$(readlink -f "$(dirname "$0")/..")"

exec watchmedo \
  auto-restart \
  --debug-force-polling \
  --directory="${rootdir}/opwen_email_server" \
  --directory="${rootdir}/opwen_email_client" \
  --pattern='*.py;*.html;*.js;*.css' \
  --recursive \
  -- "$@"
