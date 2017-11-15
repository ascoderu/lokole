#!/usr/bin/env bash

set -eo pipefail

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$DOCKER_USERNAME" -o -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

secrets_archive="$(mktemp)"
compose_file="$(mktemp)"
env_file='.env'
cert_file='cert.pem'

openssl aes-256-cbc -K $encrypted_2ff31a343d6c_key -iv $encrypted_2ff31a343d6c_iv -in travis/secrets.tar.enc -out "$secrets_archive" -d
tar xf "$secrets_archive" -C . "$cert_file" "$env_file"
touch "$env_file"

cleanup() {
  rm -f "$compose_file" "$env_file" "$secrets_archive" "$cert_file"
}
trap cleanup EXIT

APP_PORT="80" BUILD_TAG="$TRAVIS_TAG" ENV_FILE="$env_file" \
  docker-compose config > "$compose_file"

docker-compose -f "$compose_file" build

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"
docker-compose -f "$compose_file" push

if [ -z "$SERVICE_FABRIC_ENDPOINT" -o -z "$SERVICE_FABRIC_DEPLOYMENT_NAME" ]; then
  echo "No service fabric credentials configured, skipping upgrade of cluster" >&2; exit 0
fi

if [ ! -f "$cert_file" -o ! -s "$env_file" ]; then
  echo "No service fabric secrets found, unable to upgrade cluster" >&2; exit 2
fi

sudo apt-get install -y jq
sudo python3 -m pip install sfctl

sfctl cluster select --endpoint "$SERVICE_FABRIC_ENDPOINT" --pem "$cert_file" --no-verify
sfctl compose upgrade --deployment-name "$SERVICE_FABRIC_DEPLOYMENT_NAME" --file-path "$compose_file"

while [ "$(sfctl compose upgrade-status --deployment-name $SERVICE_FABRIC_DEPLOYMENT_NAME | jq -r '.upgradeState')" != 'RollingForwardCompleted' ]; do
  echo "Waiting for service fabric deployment to complete..." >&2
  sleep 15s
done

echo "All done with deployment" >&2; exit 0
