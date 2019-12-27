#!/usr/bin/env bash
set -euo pipefail

scriptdir="$(dirname "$0")"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

num_exceptions="$(sql_query 'select count(*) from exceptions;')"
num_exceptions_expected=0

if [[ "${num_exceptions}" -ne "${num_exceptions_expected}" ]]; then
  echo "Got ${num_exceptions} exceptions but expected ${num_exceptions_expected}" >&2
  exit 2
fi

num_users="$(curl -fs 'http://nginx:8888/api/email/metrics/users/developer1.lokole.ca' -u "${REGISTRATION_CREDENTIALS}" | jq -r '.users')"
num_users_expected=1

if [[ "${num_users}" -ne "${num_users_expected}" ]]; then
  echo "Got ${num_users} users but expected ${num_users_expected}" >&2
  exit 3
fi
