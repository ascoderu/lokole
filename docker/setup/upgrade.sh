#!/usr/bin/env bash

scriptdir="$(dirname "$0")"

if [[ "$1" = "vm" ]]; then
  shift
  exec "${scriptdir}/upgrade-vm.sh" "$@"
else
  exec "${scriptdir}/upgrade-helm.sh" "$@"
fi
