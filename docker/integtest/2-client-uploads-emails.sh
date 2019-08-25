#!/usr/bin/env bash
set -euo pipefail

get_dotenv() {
  local key dotenv_file

  key="$1"
  dotenv_file="$(dirname "$0")/.env"

  grep "^${key}=" "${dotenv_file}" | cut -d'=' -f2-
}

in_dir="$(dirname "$0")/files"
out_dir="$(dirname "$0")/files/test.out"
mkdir -p "${out_dir}"

emails_to_send="${in_dir}/client-emails.tar.gz"
client_id="$(jq -r '.client_id' < "${out_dir}/register1.json")"
resource_container="$(jq -r '.resource_container' < "${out_dir}/register1.json")"
resource_id="$(uuidgen).tar.gz"

# workflow 1: send emails written on the client to the world
# first we simulate the client uploading its emails to the shared blob storage
storage_account="$(get_dotenv AZURITE_ACCOUNT)"
storage_key="$(get_dotenv AZURITE_KEY)"
az storage blob upload --no-progress \
  --file "${emails_to_send}" \
  --name "${resource_id}" \
  --container-name "${resource_container}" \
  --connection-string "DefaultEndpointsProtocol=http;AccountName=${storage_account};AccountKey=${storage_key};BlobEndpoint=http://azurite:10000/${storage_account};"

# the client then calls the server to trigger the delivery of the emails
curl -fs \
  -H "Content-Type: application/json" \
  -d '{"resource_id":"'"${resource_id}"'"}' \
  "http://nginx:8888/api/email/upload/${client_id}"
