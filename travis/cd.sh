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
  BUILD_TAG="$tag" DOCKER_REPO="$DOCKER_USERNAME" USE_DEVTOOLS="False" docker-compose build
  BUILD_TAG="$tag" DOCKER_REPO="$DOCKER_USERNAME" docker-compose push

  docker build -t "$DOCKER_USERNAME/opwenserver_setup:$tag" -f "./docker/setup/Dockerfile" "."
  docker push "$DOCKER_USERNAME/opwenserver_setup:$tag"
done

#
# production deploy
#

if [[ -z "$HELM_NAME" ]] || [[ -z "$KUBECONFIG_URL" ]]; then
  echo "Skipping production deployment since no helm name or kubeconfig url is configured" >&2; exit 0
fi

kubeconfig_path="$PWD/kube-config"
curl -sfL "$KUBECONFIG_URL" -o "$kubeconfig_path"

docker run \
  -e IMAGE_REGISTRY="$DOCKER_USERNAME" \
  -e DOCKER_TAG="$TRAVIS_TAG" \
  -e HELM_NAME="$HELM_NAME" \
  -v "$kubeconfig_path:/secrets/kube-config" \
  "$DOCKER_USERNAME/opwenserver_setup:$TRAVIS_TAG" \
  /app/upgrade.sh

rm "$kubeconfig_path"

echo "All done with deployment" >&2; exit 0
