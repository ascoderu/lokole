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
##   LOKOLE_DNS_NAME
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

#
# verify inputs
#

required_env "${scriptname}" "DOCKER_TAG"
required_env "${scriptname}" "HELM_NAME"
required_env "${scriptname}" "IMAGE_REGISTRY"
required_env "${scriptname}" "LOKOLE_DNS_NAME"
required_file "${scriptname}" "/secrets/kube-config"

#
# upgrade production deployment
#

log "Upgrading helm deployment ${HELM_NAME}"

export KUBECONFIG="/secrets/kube-config"

helm_init

helm upgrade "${HELM_NAME}" \
  --set domain="${LOKOLE_DNS_NAME}" \
  --set version.imageRegistry="${IMAGE_REGISTRY}" \
  --set version.dockerTag="${DOCKER_TAG}" \
  "${scriptdir}/helm/opwen_cloudserver"
