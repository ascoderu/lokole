#!/usr/bin/env bash

set -euo pipefail

for step in lint typecheck unit-tests; do
  make "$step" -e py_env=~/virtualenv/python$TRAVIS_PYTHON_VERSION
done
