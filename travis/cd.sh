#!/usr/bin/env bash

set -eo pipefail

if [[ -z "$TRAVIS_TAG" ]]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [[ -z "$DOCKER_USERNAME" ]] || [[ -z "$DOCKER_PASSWORD" ]]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

#
# docker deploy
#

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"

for tag in "latest" "$TRAVIS_TAG"; do
  BUILD_TAG="$tag" DOCKER_REPO="$DOCKER_USERNAME" docker-compose build
  BUILD_TAG="$tag" DOCKER_REPO="$DOCKER_USERNAME" docker-compose push
done

#
# production deploy
#

if [[ -z "$HELM_NAME" ]] || [[ -z "$KUBECONFIG_URL" ]] || [[ -z "$LOKOLE_DNS_NAME" ]]; then
  echo "Skipping production deployment since connection secrets are not defined" >&2; exit 0
fi

kubeconfig_path="$PWD/kube-config"
curl -sfL "$KUBECONFIG_URL" -o "$kubeconfig_path"

docker-compose run \
  -e IMAGE_REGISTRY="$DOCKER_USERNAME" \
  -e DOCKER_TAG="$TRAVIS_TAG" \
  -e HELM_NAME="$HELM_NAME" \
  -e LOKOLE_DNS_NAME="$LOKOLE_DNS_NAME" \
  -v "$kubeconfig_path:/secrets/kube-config" \
  setup \
  /app/upgrade.sh

rm "$kubeconfig_path"

echo "All done with deployment" >&2; exit 0
