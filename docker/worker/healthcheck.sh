#!/usr/bin/env sh

healthcheck_endpoint="http://localhost/healthcheck/ping"

if ! curl --fail --silent "$healthcheck_endpoint"; then
  echo "Unable to call $healthcheck_endpoint" >&2
  exit 1
fi

exit 0
