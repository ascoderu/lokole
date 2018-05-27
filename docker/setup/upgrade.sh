#!/usr/bin/env bash
##
## This script upgrades an existing production deployment.
## The script assumes that a kubernetes secret exists at /secrets/kube-config.
##
## Required environment variables:
##
##   DOCKER_TAG
##   HELM_NAME
##   IMAGE_REGISTRY
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
. "${scriptdir}/utils.sh"

#
# verify inputs
#

required_env "${scriptname}" "DOCKER_TAG"
required_env "${scriptname}" "HELM_NAME"
required_env "${scriptname}" "IMAGE_REGISTRY"
required_file "${scriptname}" "/secrets/kube-config"

#
# upgrade production deployment
#

log "Upgrading helm deployment ${HELM_NAME}"

KUBECONFIG="/secrets/kube-config" \
helm upgrade "${HELM_NAME}" \
  --set version.imageRegistry="${IMAGE_REGISTRY}" \
  --set version.dockerTag="${DOCKER_TAG}" \
  ./helm
