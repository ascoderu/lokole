#!/usr/bin/env sh
# This docker-entrypoint populates environment variables from docker secrets.
# The docker secrets are assumed to be files in dotenv syntax. The requested
# secrets should be declared in the environment variable DOTENV_SECRETS, with
# multiple secret names separated by a semi-colon.

if [ ! -d /run/secrets ]; then
  exec "$@"
fi

if [ -z "${DOTENV_SECRETS}" ]; then
  exec "$@"
fi

eval "$(find /run/secrets -maxdepth 1 -type f | grep "$(echo "${DOTENV_SECRETS}" | sed 's/;/\\|/g')" | xargs cat | grep -v '^#' | sed 's/^\([^=]\+\)=\(.*\)$/\1="\2"; export \1;/g')"

exec "$@"
