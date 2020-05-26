#!/usr/bin/env bash

set -e

scriptdir="$(dirname "$0")"
cd "${scriptdir}/../.."

flake8 opwen_email_server opwen_email_client
isort --check-only --recursive opwen_email_server opwen_email_client
yapf --recursive --parallel --diff opwen_email_server opwen_email_client tests
bandit --recursive opwen_email_server opwen_email_client
mypy opwen_email_server opwen_email_client

coverage run -m nose2 -v
coverage xml
coverage report

if [[ -n "$1" ]]; then
  echo "$1"
  cat coverage.xml
fi
