#!/usr/bin/env bash

set -eo pipefail

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

if [ -z "$PYPI_USERNAME" ] || [ -z "$PYPI_PASSWORD" ]; then
  echo "No PyPI credentials configured, unable to publish builds" >&2; exit 1
fi

#
# setup
#

rootdir="$(readlink -f "$(dirname "$0")"/..)"

cleanup() { rm -rf "$rootdir/secrets" "$rootdir/travis/secrets.tar"; }
trap cleanup EXIT

#
# docker deploy
#

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"

touch "$rootdir/secrets/azure.env"
touch "$rootdir/secrets/sendgrid.env"

for tag in "latest" "$TRAVIS_TAG"; do
  BUILD_TAG="$tag" DOCKER_REPO="$DOCKER_USERNAME" docker-compose build
  BUILD_TAG="$tag" DOCKER_REPO="$DOCKER_USERNAME" docker-compose push

  docker build -t "$DOCKER_USERNAME/opwenserver_setup:$tag" -f "$rootdir/docker/setup/Dockerfile" "$rootdir"
  docker push "$DOCKER_USERNAME/opwenserver_setup:$tag"
done

#
# pypi deploy
#

py_env="$HOME/virtualenv/python$TRAVIS_PYTHON_VERSION"

echo "$TRAVIS_TAG" > version.txt

"$py_env/bin/pip" install twine
"$py_env/bin/python" setup.py sdist
"$py_env/bin/twine" upload -u "$PYPI_USERNAME" -p "$PYPI_PASSWORD" dist/*

#
# production deploy
#

if [ -z "$HELM_NAME" ]; then
  echo "Skipping production deployment since no helm name is configured" >&2; exit 0
fi

docker run \
  -e IMAGE_REGISTRY="$DOCKER_USERNAME" \
  -e DOCKER_TAG="$TRAVIS_TAG" \
  -e HELM_NAME="$HELM_NAME" \
  -v "$rootdir/secrets/kube-config:/secrets/kube-config" \
  "$DOCKER_USERNAME/opwenserver_setup:$TRAVIS_TAG" \
  /app/upgrade.sh

echo "All done with deployment" >&2; exit 0
