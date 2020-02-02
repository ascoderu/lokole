#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

mapfile -t containers < <(\
  az storage container list \
    --connection-string "$(az_connection_string)" \
    --query "[].name" \
    --output tsv \
  | grep "$1$")

for container in "${containers[@]}"; do
  log "Deleting container ${container}"
  az storage container delete \
    --connection-string "$(az_connection_string)" \
    --name "${container}"
done
