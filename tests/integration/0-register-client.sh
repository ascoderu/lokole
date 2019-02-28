#!/usr/bin/env bash

set -euo pipefail
out_dir="$(dirname "$0")/../files/end_to_end/test.out"
mkdir -p "${out_dir}"

# workflow 3: register a new client called "developer"
# normally this endpoint would be called during a new lokole device setup
curl -fs \
  -H "Content-Type: application/json" \
  -u "admin:password" \
  -d '{"domain":"developer.lokole.ca"}' \
  "http://localhost:8080/api/email/register/" \
| tee "${out_dir}/register.json"
