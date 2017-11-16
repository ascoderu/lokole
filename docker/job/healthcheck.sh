#!/usr/bin/env sh

if test -s "$LOKOLE_QUEUE_ERROR_FILE"; then
  cat "$LOKOLE_QUEUE_ERROR_FILE" >&2
  exit 1
fi

exit 0
