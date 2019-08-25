#!/usr/bin/env bash
set -euo pipefail

sql() {
  local postgres user database query

  postgres="$(get_container postgres)"
  user="$(get_dotenv "POSTGRES_USER")"
  database="$(get_dotenv "POSTGRES_DB")"
  query="$1"

  docker exec "${postgres}" psql -U "${user}" -d "${database}" -c "${query}"
}

sql_query() {
  local postgres

  postgres="$(get_container postgres)"

  docker exec "${postgres}" psql -Aqt -c "$1" -U ascoderu -d telemetry \
  | tr -d -C '0-9'
}

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

az_storage() {
  local mode="$1"
  local container="$2"
  local blob="$3"
  local file="$4"
  local storage_account storage_key

  storage_account="$(get_dotenv AZURITE_ACCOUNT)"
  storage_key="$(get_dotenv AZURITE_KEY)"

  az storage blob "${mode}" --no-progress \
    --file "${file}" \
    --name "${blob}" \
    --container-name "${container}" \
    --connection-string "DefaultEndpointsProtocol=http;AccountName=${storage_account};AccountKey=${storage_key};BlobEndpoint=http://azurite:10000/${storage_account};" \
  > /dev/null
}
