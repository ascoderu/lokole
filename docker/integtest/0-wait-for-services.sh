#!/usr/bin/env bash
set -euo pipefail

scriptdir="$(dirname "$0")"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

readonly polling_interval_seconds=2

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
