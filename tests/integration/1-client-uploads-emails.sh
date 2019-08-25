#!/usr/bin/env bash
set -euo pipefail

in_dir="$(dirname "$0")/../files/end_to_end"
out_dir="$(dirname "$0")/../files/end_to_end/test.out"
mkdir -p "${out_dir}"

emails_to_send="${in_dir}/client-emails.tar.gz"
client_id="$(jq -r '.client_id' < "${out_dir}/register1.json")"
resource_container="$(jq -r '.resource_container' < "${out_dir}/register1.json")"
resource_id="$(uuidgen).tar.gz"

# workflow 1: send emails written on the client to the world
# first we simulate the client uploading its emails to the shared blob storage
az storage blob upload --no-progress \
  --file "${emails_to_send}" \
  --name "${resource_id}" \
  --container-name "${resource_container}" \
  --connection-string "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"

# the client then calls the server to trigger the delivery of the emails
curl -fs \
  -H "Content-Type: application/json" \
  -d '{"resource_id":"'"${resource_id}"'"}' \
  "http://nginx:8888/api/email/upload/${client_id}"
