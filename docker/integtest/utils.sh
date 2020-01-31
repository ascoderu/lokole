#!/usr/bin/env bash
set -euo pipefail

get_container() {
  docker ps --format  '{{.Names}}' | grep "$1"
}

get_dotenv() {
  local key dotenv_file

  key="$1"
  dotenv_file="$(dirname "$0")/.env"

  grep "^${key}=" "${dotenv_file}" | cut -d'=' -f2-
}

log() {
  echo "$@" >&2
}

appinsights_container() {
  get_dotenv "APPINSIGHTS_INSTRUMENTATIONKEY" | tr -d '-'
}

az_connection_string() {
  local storage_account storage_key

  storage_account="$(get_dotenv AZURITE_ACCOUNT)"
  storage_key="$(get_dotenv AZURITE_KEY)"

  echo "DefaultEndpointsProtocol=http;AccountName=${storage_account};AccountKey=${storage_key};BlobEndpoint=http://azurite:10000/${storage_account};"
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
