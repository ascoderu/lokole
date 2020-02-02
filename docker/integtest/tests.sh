#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"

"${scriptdir}/0-wait-for-services.sh"
"${scriptdir}/1-register-client.sh"
"${scriptdir}/2-client-uploads-emails.sh" && sleep 10s
"${scriptdir}/3-receive-email-for-client.sh" && sleep 10s
"${scriptdir}/4-client-downloads-emails.sh"
"${scriptdir}/5-assert-on-results.sh"

rm -rf "${scriptdir}/files/test.out"
