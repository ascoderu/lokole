#!/usr/bin/env bash

set -eo pipefail

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$PYPI_USERNAME" ] || [ -z "$PYPI_PASSWORD" ]; then
  echo "No PyPI credentials configured, unable to publish builds" >&2; exit 1
fi

if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

echo "$TRAVIS_TAG" > version.txt

py_env="$HOME/virtualenv/python$TRAVIS_PYTHON_VERSION"

make prepare-server -e py_env="$py_env" -e NPM="$(which npm)" -e SHELLCHECK="$(which shellcheck)"

"$py_env/bin/pip" install twine
"$py_env/bin/python" setup.py sdist
"$py_env/bin/twine" upload -u "$PYPI_USERNAME" -p "$PYPI_PASSWORD" dist/*

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"

docker build \
  --build-arg "CLIENT_VERSION=$TRAVIS_TAG" \
  --tag "$DOCKER_USERNAME/opwenclient_app:$TRAVIS_TAG" \
  docker/app

docker push "$DOCKER_USERNAME/opwenclient_app:$TRAVIS_TAG"

docker tag "$DOCKER_USERNAME/opwenclient_app:$TRAVIS_TAG" "$DOCKER_USERNAME/opwenclient_app:latest"
docker push "$DOCKER_USERNAME/opwenclient_app:latest"
