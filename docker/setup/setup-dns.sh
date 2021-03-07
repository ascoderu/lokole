#!/usr/bin/env bash
##
## This script sets the required DNS records for a Lokole server deployment.
## The script assumes that Cloudflare credentials exists at /secrets/cloudflare.env.
##
## Required environment variables:
##
##   LOKOLE_SERVER_IP
##   LOKOLE_DNS_NAME
##

scriptdir="$(dirname "$0")"
scriptname="${BASH_SOURCE[0]}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

#
# verify inputs
#

required_env "${scriptname}" "LOKOLE_SERVER_IP"
required_env "${scriptname}" "LOKOLE_DNS_NAME"
required_file "${scriptname}" "/secrets/cloudflare.env"

#
# configure dns
#

log "Setting up DNS mapping ${LOKOLE_SERVER_IP} to ${LOKOLE_DNS_NAME}"

cloudflare_zone="$(get_dotenv '/secrets/cloudflare.env' 'LOKOLE_CLOUDFLARE_ZONE')"
cloudflare_user="$(get_dotenv '/secrets/cloudflare.env' 'LOKOLE_CLOUDFLARE_USER')"
cloudflare_key="$(get_dotenv '/secrets/cloudflare.env' 'LOKOLE_CLOUDFLARE_KEY')"
cloudflare_dns_api="https://api.cloudflare.com/client/v4/zones/${cloudflare_zone}/dns_records"

cloudflare_cname_id="$(curl -sX GET "${cloudflare_dns_api}?type=A&name=${LOKOLE_DNS_NAME}" \
  -H "X-Auth-Email: ${cloudflare_user}" \
  -H "X-Auth-Key: ${cloudflare_key}" |
  jq -r '.result[0].id')"

if [[ -n "${cloudflare_cname_id}" ]] && [[ ${cloudflare_cname_id} != "null" ]]; then
  curl -sX PUT "${cloudflare_dns_api}/${cloudflare_cname_id}" \
    -H "X-Auth-Email: ${cloudflare_user}" \
    -H "X-Auth-Key: ${cloudflare_key}" \
    -H "Content-Type: application/json" \
    -d '{"type":"A","name":"'"${LOKOLE_DNS_NAME}"'","content":"'"${LOKOLE_SERVER_IP}"'","ttl":1,"proxied":false}'
else
  curl -sX POST "${cloudflare_dns_api}" \
    -H "X-Auth-Email: ${cloudflare_user}" \
    -H "X-Auth-Key: ${cloudflare_key}" \
    -H "Content-Type: application/json" \
    -d '{"type":"A","name":"'"${LOKOLE_DNS_NAME}"'","content":"'"${LOKOLE_SERVER_IP}"'","ttl":1,"proxied":false}'
fi
