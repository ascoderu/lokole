#!/usr/bin/env bash
##
## This script upgrades an production VM.
##
## Required environment variables:
##
##   LOKOLE_VM_PASSWORD
##   LOKOLE_DNS_NAME
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

#
# verify inputs
#

required_env "${scriptname}" "LOKOLE_VM_PASSWORD"
required_env "${scriptname}" "LOKOLE_DNS_NAME"

#
# upgrade production deployment
#

log "Upgrading VM ${LOKOLE_DNS_NAME}"

exec sshpass -p "${LOKOLE_VM_PASSWORD}" ssh -o StrictHostKeyChecking=no "opwen@${LOKOLE_DNS_NAME}" <"${scriptdir}/vm.sh"
