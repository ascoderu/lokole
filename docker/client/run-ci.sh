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

# Run only client tests
coverage run -m nose2 -v tests.opwen_email_client
coverage xml
coverage report

if [[ -n "$1" ]]; then
  echo "$1"
  cat coverage.xml
fi
