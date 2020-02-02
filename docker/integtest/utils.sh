#!/usr/bin/env bash
set -eo pipefail

get_container() {
  docker ps --format  '{{.Names}}' | grep "$1"
}

log() {
  echo "$@" >&2
}

appinsights_container() {
  tr -d '-' <<< "${APPINSIGHTS_INSTRUMENTATIONKEY}"
}

az_connection_string() {
  echo "AccountName=${AZURITE_ACCOUNT};AccountKey=${AZURITE_KEY};DefaultEndpointsProtocol=http;BlobEndpoint=http://azurite:10000/${AZURITE_ACCOUNT};"
}

az_storage() {
  local mode="$1"
  local container="$2"
  local blob="$3"
  local file="$4"

  az storage blob "${mode}" --no-progress \
    --file "${file}" \
    --name "${blob}" \
    --container-name "${container}" \
    --connection-string "$(az_connection_string)" \
  > /dev/null
}
