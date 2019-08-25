#!/usr/bin/env bash
set -euo pipefail

scriptdir="$(dirname "$0")"
out_dir="${scriptdir}/files/test.out"
mkdir -p "${out_dir}"
# shellcheck disable=SC1090
. "${scriptdir}/utils.sh"

# workflow 3: register a new client called "developer"
# normally this endpoint would be called during a new lokole device setup
curl -fs \
  -H "Content-Type: application/json" \
  -u "admin:password" \
  -d '{"domain":"developer1.lokole.ca"}' \
  "http://nginx:8888/api/email/register/" \
| tee "${out_dir}/register1.json"

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
  -u "admin:password" \
  -d '{"domain":"developer2.lokole.ca"}' \
  "http://nginx:8888/api/email/register/" \
| tee "${out_dir}/register2.json"
