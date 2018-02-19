#!/usr/bin/env sh

if ! curl --fail --silent "http://api_email_receive:8001/healthcheck/ping"; then
  echo "Unable to call api_email_receive" >&2
  exit 1
fi

if ! curl --fail --silent "http://api_client_write:8002/healthcheck/ping"; then
  echo "Unable to call api_client_write" >&2
  exit 2
fi

if ! curl --fail --silent "http://api_client_read:8003/healthcheck/ping"; then
  echo "Unable to call api_client_read" >&2
  exit 3
fi

exit 0
