#!/usr/bin/env bash

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$DOCKERIO_USERNAME" -o -z "$DOCKERIO_PASSWORD" ]; then
  echo "No docker.io credentials configured, unable to publish builds" >&2; exit 1
fi

set -euo pipefail

compose_file="$(mktemp)"
env_file="$(mktemp)"

cleanup() {
  rm -f "$compose_file" "$env_file"
}
trap cleanup EXIT

APP_PORT="80" BUILD_TAG="$TRAVIS_TAG" ENV_FILE="$env_file" docker-compose config > "$compose_file"

docker-compose -f "$compose_file" build

docker login --username="$DOCKERIO_USERNAME" --password="$DOCKERIO_PASSWORD"

< "$compose_file" grep -Po '(?<=image: ).*$' | sort -u | while read image; do
  docker push "$image"
done
