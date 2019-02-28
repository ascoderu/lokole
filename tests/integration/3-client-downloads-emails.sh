#!/usr/bin/env bash

set -euo pipefail
data_dir="$(dirname "$0")/../files/end_to_end"

client_id="$(jq -r '.client_id' < "${data_dir}/register.json")"
resource_container="$(jq -r '.resource_container' < "${data_dir}/register.json")"

# workflow 2b: deliver emails written by the world to a lokole client
# first the client makes a request to ask the server to package up all the
# emails sent from the world to the client during the last period; the server
# will package up the emails and store them on the shared blob storage
curl -fs \
  -H "Accept: application/json" \
  "http://localhost:8080/api/email/download/${client_id}" \
| tee "${data_dir}/download.json"

resource_id="$(jq -r '.resource_id' < "${data_dir}/download.json")"

# now we simulate the client downloading the package from the shared blob storage
curl -fs \
  "http://localhost:10000/devstoreaccount1/${resource_container}/${resource_id}" \
> "${data_dir}/downloaded.tar.gz"

tar xzf "${data_dir}/downloaded.tar.gz" -C "${data_dir}"

num_emails_actual="$(wc -l "${data_dir}/emails.jsonl" | cut -d' ' -f1)"
num_emails_expected=1

if [[ "${num_emails_actual}" -ne "${num_emails_expected}" ]]; then
  echo "Got ${num_emails_actual} but expected ${num_emails_expected}" >&2
  exit 1
fi
