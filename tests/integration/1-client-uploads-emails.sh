#!/usr/bin/env bash

set -euo pipefail
data_dir="$(dirname "$0")/../files/end_to_end"

emails_to_send="${data_dir}/client-emails.tar.gz"
client_id="$(jq -r '.client_id' < "${data_dir}/register.json")"
resource_container="$(jq -r '.resource_container' < "${data_dir}/register.json")"
resource_id="$(python3 -c 'import uuid;print(str(uuid.uuid4()))').tar.gz"

# workflow 1: send emails written on the client to the world
# first we simulate the client uploading its emails to the shared blob storage
curl -fs \
  -X PUT -T "${emails_to_send}" \
  -H "x-ms-blob-type: BlockBlob" \
  -H "Content-Length: $(wc -c "${emails_to_send}" | cut -d' ' -f1)" \
  "http://localhost:10000/devstoreaccount1/${resource_container}/${resource_id}"

# the client then calls the server to trigger the delivery of the emails
curl -fs \
  -H "Content-Type: application/json" \
  -d '{"resource_id":"'"${resource_id}"'"}' \
  "http://localhost:8080/api/email/upload/${client_id}"
