#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

readonly polling_interval_seconds=2
readonly max_retries=30

wait_for_rabbitmq() {
  local rabbitmq
  local i

  rabbitmq="$(get_container rabbitmq)"

  for i in $(seq 1 "${max_retries}"); do
    if docker exec "${rabbitmq}" rabbitmqctl wait -q -P 1 -t "${polling_interval_seconds}"; then
      log "Rabbitmq is running"
      return
    fi
    log "Waiting for rabbitmq (${i}/${max_retries})"
  done

  exit 1
}

wait_for_appinsights() {
  local i

  for i in $(seq 1 "${max_retries}"); do
    if [[ \
      "$(az storage container exists \
        --name "${APPINSIGHTS_INSTRUMENTATIONKEY}" \
        --connection-string "$(az_connection_string)" \
        --output tsv)" = "True" ]] \
        ; then
      log "Appinsights is running"
      return
    fi
    log "Waiting for appinsights (${i}/${max_retries})"
    sleep "${polling_interval_seconds}s"
  done

  exit 3
}

wait_for_api() {
  local i

  for i in $(seq 1 "${max_retries}"); do
    if curl -fs "http://nginx:8888/healthcheck/ping" >/dev/null; then
      log "Api is running"
      return
    fi
    log "Waiting for api (${i}/${max_retries})"
    sleep "${polling_interval_seconds}s"
  done

  exit 4
}

wait_for_webapp() {
  local i

  for i in $(seq 1 "${max_retries}"); do
    if curl -fs "http://nginx:8888/web/healthcheck/ping" >/dev/null; then
      log "Webapp is running"
      return
    fi
    log "Waiting for webapp (${i}/${max_retries})"
    sleep "${polling_interval_seconds}s"
  done

  exit 4
}

wait_for_client() {
  local i

  for i in $(seq 1 "${max_retries}"); do
    if curl -fs "http://client:5000/healthcheck/ping" >/dev/null; then
      log "Client is running"
      return
    fi
    log "Waiting for client (${i}/${max_retries})"
    sleep "${polling_interval_seconds}s"
  done

  exit 5
}

wait_for_rabbitmq
wait_for_appinsights
wait_for_api
wait_for_webapp
wait_for_client
