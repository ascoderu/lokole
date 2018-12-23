#!/usr/bin/env bash

set -eo pipefail

if [[ -z "$TRAVIS_PYTHON_VERSION" ]]; then
  echo "Build is not targeting a Python version, can't run CI" >&2; exit 1
fi

make ci -e py_env="$HOME/virtualenv/python$TRAVIS_PYTHON_VERSION"
