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
