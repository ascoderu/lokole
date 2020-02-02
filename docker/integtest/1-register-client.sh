#!/usr/bin/env bash
set -eo pipefail

scriptdir="$(dirname "$0")"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

# workflow 3: register a new client called "developer"
# normally this endpoint would be called during a new lokole device setup
curl -fs \
  -H "Content-Type: application/json" \
  -u "${REGISTRATION_CREDENTIALS}" \
  -d '{"domain":"developer1.lokole.ca"}' \
  "http://nginx:8888/api/email/register/"

while ! curl -fs -u "${REGISTRATION_CREDENTIALS}" "http://nginx:8888/api/email/register/developer1.lokole.ca" | tee "${out_dir}/register1.json"; do
  log "Waiting for client 1 registration"
  sleep 1s
done

# registering a client with bad credentials should fail
if curl -fs \
  -H "Content-Type: application/json" \
  -u "baduser:badpassword" \
  -d '{"domain":"hacker.lokole.ca"}' \
  "http://nginx:8888/api/email/register/" \
; then echo "Was able to register a client with bad credentials" >&2; exit 4; fi

# also register another client to simulate multi-client emails
curl -fs \
  -H "Content-Type: application/json" \
  -u "${REGISTRATION_CREDENTIALS}" \
  -d '{"domain":"developer2.lokole.ca"}' \
  "http://nginx:8888/api/email/register/"

while ! curl -fs -u "${REGISTRATION_CREDENTIALS}" "http://nginx:8888/api/email/register/developer2.lokole.ca" | tee "${out_dir}/register2.json"; do
  log "Waiting for client 2 registration"
  sleep 1s
done

# after creating a client, creating the same one again should fail but we should be able to delete it
curl -fs \
  -H "Content-Type: application/json" \
  -u "${REGISTRATION_CREDENTIALS}" \
  -d '{"domain":"developer3.lokole.ca"}' \
  "http://nginx:8888/api/email/register/"

while ! curl -fs -u "${REGISTRATION_CREDENTIALS}" "http://nginx:8888/api/email/register/developer3.lokole.ca"; do
  log "Waiting for client 3 registration"
  sleep 1s
done

if curl -fs \
  -H "Content-Type: application/json" \
  -u "${REGISTRATION_CREDENTIALS}" \
  -d '{"domain":"developer3.lokole.ca"}' \
  "http://nginx:8888/api/email/register/" \
; then echo "Was able to register a duplicate client" >&2; exit 5; fi

curl -fs \
  -u "${REGISTRATION_CREDENTIALS}" \
  -X DELETE \
  "http://nginx:8888/api/email/register/developer3.lokole.ca"
