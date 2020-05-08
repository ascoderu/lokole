#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

"${scriptdir}/0-wait-for-services.sh"
"${scriptdir}/1-register-client.sh"
"${scriptdir}/2-client-uploads-emails.sh" && wait_seconds "${TEST_STEP_DELAY}"
"${scriptdir}/3-receive-email-for-client.sh" && wait_seconds "${TEST_STEP_DELAY}"
"${scriptdir}/4-client-downloads-emails.sh"
"${scriptdir}/5-assert-on-results.sh"
"${scriptdir}/6-receive-service-email.sh"

rm -rf "${scriptdir}/files/test.out"
