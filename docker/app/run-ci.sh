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

# Run only server tests
coverage run -m nose2 -v tests.opwen_email_server
coverage xml
coverage report

if [[ -n "$1" ]]; then
  echo "$1"
  cat coverage.xml
fi
