#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

readonly polling_interval_seconds=2
readonly max_retries=150

wait_for_client() {
  local client="$1"
  local i

  for i in $(seq 1 "${max_retries}"); do
    if authenticated_request "http://nginx:8888/api/email/register/developer${client}.lokole.ca" >"${out_dir}/register${client}.json"; then
      log "Client ${client} is registered"
      return
    fi
    log "Waiting for client ${client} registration (${i}/${max_retries})"
    sleep "${polling_interval_seconds}"
  done

  exit 1
}

# workflow 3: register a new client called "developer"
# normally this endpoint would be called during a new lokole device setup
authenticated_request \
  "http://nginx:8888/api/email/register/" \
  -H "Content-Type: application/json" \
  -d '{"domain":"developer1.lokole.ca"}'

wait_for_client 1

# registering a client with bad credentials should fail
if REGISTRATION_CREDENTIALS="baduser:badpassword" authenticated_request \
  "http://nginx:8888/api/email/register/" \
  -H "Content-Type: application/json" \
  -d '{"domain":"hacker.lokole.ca"}' \
  ; then
  echo "Was able to register a client with bad basic auth credentials" >&2
  exit 4
fi

if REGISTRATION_CREDENTIALS="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" authenticated_request \
  "http://nginx:8888/api/email/register/" \
  -H "Content-Type: application/json" \
  -d '{"domain":"hacker.lokole.ca"}' \
  ; then
  echo "Was able to register a client with bad bearer credentials" >&2
  exit 4
fi

# also register another client to simulate multi-client emails
authenticated_request \
  "http://nginx:8888/api/email/register/" \
  -H "Content-Type: application/json" \
  -d '{"domain":"developer2.lokole.ca"}'

wait_for_client 2

# after creating a client, creating the same one again should fail but we should be able to delete it
authenticated_request \
  "http://nginx:8888/api/email/register/" \
  -H "Content-Type: application/json" \
  -d '{"domain":"developer3.lokole.ca"}'

wait_for_client 3

if authenticated_request \
  "http://nginx:8888/api/email/register/" \
  -H "Content-Type: application/json" \
  -d '{"domain":"developer3.lokole.ca"}' \
  ; then
  echo "Was able to register a duplicate client" >&2
  exit 5
fi

authenticated_request \
  "http://nginx:8888/api/email/register/developer3.lokole.ca" \
  -X DELETE
