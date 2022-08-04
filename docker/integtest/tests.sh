#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

log "### 0-wait-for-services.sh"
"${scriptdir}/0-wait-for-services.sh"

log "### 1-register-client.sh"
"${scriptdir}/1-register-client.sh"

log "### 2-client-uploads-emails.sh"
"${scriptdir}/2-client-uploads-emails.sh" && wait_seconds "${TEST_STEP_DELAY}"

log "### 3-receive-email-for-client.sh"
"${scriptdir}/3-receive-email-for-client.sh" && wait_seconds "${TEST_STEP_DELAY}"

# TODO: debug failures
# log "### 4-client-downloads-emails.sh"
# "${scriptdir}/4-client-downloads-emails.sh"

# log "### 5-assert-on-results.sh"
# "${scriptdir}/5-assert-on-results.sh"

# log "### 6-receive-service-email.sh"
# "${scriptdir}/6-receive-service-email.sh"

rm -rf "${scriptdir}/files/test.out"
