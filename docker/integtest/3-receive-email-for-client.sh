#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
in_dir="${scriptdir}/files"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

email_to_receive="${in_dir}/inbound-email.mime"

if [[ -n "$1" ]]; then
  client_id="$1"
else
  client_id="$(jq -r '.client_id' <"${out_dir}/register1.json")"
fi

# workflow 2a: receive an email directed at one of the clients
# this simulates sendgrid delivering an email to the service
http --ignore-stdin --check-status -f POST \
  "http://nginx:8888/api/email/sendgrid/${client_id}" \
  "dkim={@sendgrid.com : pass}" \
  "SPF=pass" \
  "email=@${email_to_receive}"

# simulate delivery of the same email to the second mailbox
http --ignore-stdin --check-status -f POST \
  "http://nginx:8888/api/email/sendgrid/${client_id}" \
  "dkim={@sendgrid.com : pass}" \
  "SPF=pass" \
  "email=@${email_to_receive}"

# simulate delivery of another email
http --ignore-stdin --check-status -f POST \
  "http://nginx:8888/api/email/sendgrid/${client_id}" \
  "dkim={@sendgrid.com : pass}" \
  "SPF=pass" \
  "email=@${in_dir}/inbound-email-2.mime"
