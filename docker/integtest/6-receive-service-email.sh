#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
in_dir="${scriptdir}/files"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

email_to_receive="${in_dir}/inbound-email.mime"


#receive an email directed at the service endpoint
http --check-status -f POST \
  "http://nginx:8888/api/email/sendgrid/service" \
  "dkim={@sendgrid.com : pass}" \
  "SPF=pass" \
  "email=@${email_to_receive}"
