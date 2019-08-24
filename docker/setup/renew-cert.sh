#!/usr/bin/env bash
##
## This script renews the LetsEncrypt certificate for the cluster.
## The script assumes that a kubernetes secret exists at /secrets/kube-config.
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

#
# verify inputs
#

required_file "${scriptname}" "/secrets/kube-config"

#
# delete kube-lego pod: the pod will be automatically re-created which will
# force a refresh of the https certificate if required
#

export KUBECONFIG="/secrets/kube-config"

log "Looking up current kube-lego pods"
kubectl get pod -l app=kube-lego

log "Re-creating kube-lego pod"
kubectl delete pod -l app=kube-lego

log "Looking up new kube-lego pods"
kubectl get pod -l app=kube-lego
