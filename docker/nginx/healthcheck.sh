#!/usr/bin/env sh

if ! curl --fail --silent "http://apiemailreceive/healthcheck/ping"; then
  echo "Unable to call apiemailreceive" >&2
  exit 1
fi

if ! curl --fail --silent "http://apiclientwrite/healthcheck/ping"; then
  echo "Unable to call apiclientwrite" >&2
  exit 2
fi

if ! curl --fail --silent "http://apiclientread/healthcheck/ping"; then
  echo "Unable to call apiclientread" >&2
  exit 3
fi

exit 0
