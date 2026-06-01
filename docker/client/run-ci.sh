#!/usr/bin/env bash

set -e

scriptdir="$(dirname "$0")"
cd "${scriptdir}/../.."

# Client CI only tests client code (Python 3.12)
flake8 opwen_email_client
isort --check-only opwen_email_client
yapf --recursive --parallel --diff opwen_email_client tests/opwen_email_client
bandit --recursive opwen_email_client
mypy opwen_email_client

# Run only client tests with client-only coverage
coverage run --source=opwen_email_client -m nose2 -v tests.opwen_email_client
coverage xml
# Note: No coverage threshold check - test-local job enforces 75% combined coverage

if [[ -n "$1" ]]; then
  echo "$1"
  cat coverage.xml
fi
