#!/usr/bin/env bash

if [ -z "$TRAVIS_PYTHON_VERSION" ]; then
  echo "Build is not targetting a Python version, can't run CI" >&2; exit 1
fi

set -euo pipefail

make ci -e py_env=~/virtualenv/python$TRAVIS_PYTHON_VERSION
