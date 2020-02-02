#!/usr/bin/env bash
set -eo pipefail

get_container() {
  docker ps --format  '{{.Names}}' | grep "$1"
}

log() {
  echo "$@" >&2
}

az_connection_string() {
  if [[ -z "${AZURITE_HOST}" ]]; then
    echo "AccountName=${AZURITE_ACCOUNT};AccountKey=${AZURITE_KEY};"
  else
    echo "AccountName=${AZURITE_ACCOUNT};AccountKey=${AZURITE_KEY};BlobEndpoint=http://${AZURITE_HOST}/${AZURITE_ACCOUNT};"
  fi
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
