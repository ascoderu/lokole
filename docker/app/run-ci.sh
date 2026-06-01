#!/usr/bin/env bash

set -e

scriptdir="$(dirname "$0")"
cd "${scriptdir}/../.."

# Server CI only tests server code (Python 3.9)
flake8 opwen_email_server
isort --check-only opwen_email_server
yapf --recursive --parallel --diff opwen_email_server tests/opwen_email_server
bandit --recursive opwen_email_server
mypy opwen_email_server

# Run only server tests with server-only coverage
coverage run --source=opwen_email_server -m nose2 -v tests.opwen_email_server
coverage xml --fail-under=0
# Note: No coverage threshold check - test-local job enforces 75% combined coverage

if [[ -n "$1" ]]; then
  echo "$1"
  cat coverage.xml
fi
