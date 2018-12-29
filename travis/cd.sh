#!/usr/bin/env bash

set -eo pipefail

if [[ -z "$TRAVIS_TAG" ]]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [[ -z "$PYPI_USERNAME" ]] || [[ -z "$PYPI_PASSWORD" ]]; then
  echo "No PyPI credentials configured, unable to publish builds" >&2; exit 1
fi

echo "$TRAVIS_TAG" > version.txt

py_env="$HOME/virtualenv/python$TRAVIS_PYTHON_VERSION"

make prepare-server -e py_env="$py_env"

"$py_env/bin/pip" install twine
"$py_env/bin/python" setup.py sdist
"$py_env/bin/twine" upload -u "$PYPI_USERNAME" -p "$PYPI_PASSWORD" dist/*
