#!/usr/bin/env bash
set -euo pipefail

root_dir="$(dirname "$0")"

"${root_dir}/0-wait-for-services.sh"
"${root_dir}/1-register-client.sh"
"${root_dir}/2-client-uploads-emails.sh" && sleep 10s
"${root_dir}/3-receive-email-for-client.sh" && sleep 10s
"${root_dir}/4-client-downloads-emails.sh"
"${root_dir}/5-assert-on-results.sh"

rm -rf "${root_dir}/files/test.out"
