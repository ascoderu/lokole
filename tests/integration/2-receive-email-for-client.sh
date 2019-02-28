#!/usr/bin/env bash

set -euo pipefail
data_dir="$(dirname "$0")/../files/end_to_end"

email_to_receive="${data_dir}/inbound-email.mime"

client_id="$(jq -r '.client_id' < "${data_dir}/register.json")"

# workflow 2a: receive an email directed at one of the clients
# this simulates sendgrid delivering an email to the service
curl -fs \
  -H "Content-Type: multipart/form-data" \
  -F "email=$(cat "${email_to_receive}")" \
  "http://localhost:8080/api/email/sendgrid/${client_id}"
