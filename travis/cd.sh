#!/usr/bin/env bash

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$DOCKER_USERNAME" -o -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

set -euo pipefail

secrets_archive="$(mktemp)"
compose_file="$(mktemp)"
env_file='.env'

openssl aes-256-cbc -K $encrypted_2ff31a343d6c_key -iv $encrypted_2ff31a343d6c_iv -in travis/secrets.tar.enc -out "$secrets_archive" -d
tar xf "$secrets_archive" -C . "$cert_file" "$env_file"
touch "$env_file"

cleanup() {
  rm -f "$compose_file" "$env_file" "$secrets_archive"
}
trap cleanup EXIT

APP_PORT="80" BUILD_TAG="$TRAVIS_TAG" ENV_FILE="$env_file" \
  docker-compose config > "$compose_file"

docker-compose -f "$compose_file" build

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"
docker-compose -f "$compose_file" push

