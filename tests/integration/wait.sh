#!/usr/bin/env bash
set -euo pipefail

readonly polling_interval_seconds=2

log() {
  echo "$@" >&2
}

get_dotenv() {
  local key dotenv_file

  key="$1"
  dotenv_file="$(dirname "$0")/../../.env"

  grep "^${key}=" "${dotenv_file}" | cut -d'=' -f2-
}

get_container() {
  docker ps --format  '{{.Names}}' | grep "$1"
}

sql() {
  local postgres user database query

  postgres="$(get_container postgres)"
  user="$(get_dotenv "POSTGRES_USER")"
  database="$(get_dotenv "POSTGRES_DB")"
  query="$1"

  docker exec "${postgres}" psql -U "${user}" -d "${database}" -c "${query}"
}

wait_for_rabbitmq() {
  local rabbitmq

  rabbitmq="$(get_container rabbitmq)"

  while ! docker exec "${rabbitmq}" rabbitmqctl wait -q -P 1 -t "${polling_interval_seconds}"; do
    log "Waiting for rabbitmq"
  done

  log "Rabbitmq is running"
}

wait_for_postgres() {
  while ! sql "select 1;" >/dev/null; do
    log "Waiting for postgres"
    sleep "${polling_interval_seconds}s"
  done

  log "Postgres is running"
}

wait_for_appinsights() {
  local key

  key="$(get_dotenv "APPINSIGHTS_INSTRUMENTATIONKEY")"

  while ! sql "select 'ready' from clients where client = '${key}';" | grep -q 'ready'; do
    log "Waiting for appinsights"
    sleep "${polling_interval_seconds}s"
  done

  log "Appinsights is running"
}

wait_for_rabbitmq
wait_for_postgres
wait_for_appinsights
