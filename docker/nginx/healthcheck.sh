#!/usr/bin/env sh

if ! curl --fail --silent "http://${HOSTNAME_EMAIL_RECEIVE}/healthcheck/ping"; then
  echo "Unable to call ${HOSTNAME_EMAIL_RECEIVE}" >&2
  exit 1
fi

if ! curl --fail --silent "http://${HOSTNAME_CLIENT_WRITE}/healthcheck/ping"; then
  echo "Unable to call ${HOSTNAME_CLIENT_WRITE}" >&2
  exit 2
fi

if ! curl --fail --silent "http://${HOSTNAME_CLIENT_READ}/healthcheck/ping"; then
  echo "Unable to call ${HOSTNAME_CLIENT_READ}" >&2
  exit 3
fi

exit 0
