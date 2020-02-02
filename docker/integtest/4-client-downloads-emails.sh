#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

for i in 1 2; do

client_id="$(jq -r '.client_id' < "${out_dir}/register${i}.json")"
resource_container="$(jq -r '.resource_container' < "${out_dir}/register${i}.json")"

# workflow 2b: deliver emails written by the world to a lokole client
# first the client makes a request to ask the server to package up all the
# emails sent from the world to the client during the last period; the server
# will package up the emails and store them on the shared blob storage
curl -fs \
  -H "Accept: application/json" \
  "http://nginx:8888/api/email/download/${client_id}" \
| tee "${out_dir}/download${i}.json"

resource_id="$(jq -r '.resource_id' < "${out_dir}/download${i}.json")"

# now we simulate the client downloading the package from the shared blob storage
az_storage download "${resource_container}" "${resource_id}" "${out_dir}/downloaded${i}.tar.gz"

tar xzf "${out_dir}/downloaded${i}.tar.gz" -C "${out_dir}"

num_emails_actual="$(wc -l "${out_dir}/emails.jsonl" | cut -d' ' -f1)"
num_emails_expected=1

if [[ "${num_emails_actual}" -ne "${num_emails_expected}" ]]; then
  echo "Got ${num_emails_actual} emails but expected ${num_emails_expected}" >&2
  exit 1
fi

rm "${out_dir}/emails.jsonl"

done
