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

APP_PORT="$app_port" BUILD_TAG="$build_tag" ENV_FILE="$env_file" \
  docker-compose config > "$compose_file"

docker-compose -f "$compose_file" build

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"
docker-compose -f "$compose_file" push

