#!/usr/bin/env bash

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$DOCKER_USERNAME" -o -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

set -euo pipefail

compose_file="$(mktemp)"
env_file="$(mktemp)"

app_port="80"
build_tag="$TRAVIS_TAG"

cleanup() {
  rm -f "$compose_file" "$env_file"
}
trap cleanup EXIT

make -e build_tag="$build_tag" -e env_file="$env_file" -e app_port="$app_port" \
  docker-build

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"

make -e build_tag="$build_tag" -e env_file="$env_file" -e app_port="$app_port" \
  docker-push
