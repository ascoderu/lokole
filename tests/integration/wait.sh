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

wait_for_rabbitmq() {
  while ! docker-compose exec rabbitmq rabbitmqctl wait -q -P 1 -t "${polling_interval_seconds}"; do
    log "Waiting for rabbitmq"
  done

  log "Rabbitmq is running"
}

wait_for_postgres() {
  local user database

  user="$(get_dotenv "POSTGRES_USER")"
  database="$(get_dotenv "POSTGRES_DB")"

  while ! docker-compose exec postgres psql -U "${user}" -d "${database}" -c "select 1;" >/dev/null; do
    log "Waiting for postgres"
    sleep "${polling_interval_seconds}s"
  done

  log "Postgres is running"
}

wait_for_appinsights() {
  local port host

  port="$(get_dotenv "APPINSIGHTS_PORT")"
  host="localhost"

  while ! nc -z "${host}" "${port}"; do
    log "Waiting for appinsights"
    sleep "${polling_interval_seconds}s"
  done

  log "Appinsights is running"
}

wait_for_rabbitmq
wait_for_postgres
wait_for_appinsights
