#!/usr/bin/env bash
set -euo pipefail

out_dir="$(dirname "$0")/files/test.out"
mkdir -p "${out_dir}"

get_container() {
  docker ps --format  '{{.Names}}' | grep "$1"
}

sql_query() {
  local postgres

  postgres="$(get_container postgres)"

  docker exec "${postgres}" psql -Aqt -c "$1" -U ascoderu -d telemetry \
  | tr -d -C '0-9'
}

num_exceptions="$(sql_query 'select count(*) from exceptions;')"
num_exceptions_expected=0

if [[ "${num_exceptions}" -ne "${num_exceptions_expected}" ]]; then
  echo "Got ${num_exceptions} exceptions but expected ${num_exceptions_expected}" >&2
  exit 2
fi
