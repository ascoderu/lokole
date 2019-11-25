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
# delete cert-manager pod: the pod will be automatically re-created which will
# force a refresh of the https certificate if required
#

export KUBECONFIG="/secrets/kube-config"

log "Looking up current cert-manager pods"
kubectl get pod -l certmanager.k8s.io/acme-http01-solver=true
kubectl get pod -n cert-manager

log "Re-creating cert-manager pod"
kubectl delete pod -l certmanager.k8s.io/acme-http01-solver=true
kubectl delete pod -n cert-manager -l app=cert-manager

log "Looking up new cert-manager pods"
kubectl get pod -l certmanager.k8s.io/acme-http01-solver=true
kubectl get pod -n cert-manager
