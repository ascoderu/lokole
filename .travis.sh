#!/usr/bin/env bash

set -eo pipefail

if [[ "$TRAVIS_PULL_REQUEST" = "false" ]] && [[ "$TEST_MODE" = "live" ]]; then
  echo "Skipping live service CI for branch build" >&2
  exit 0
fi

if [[ "$TRAVIS_PULL_REQUEST_SLUG" != "ascoderu/lokole" ]] && [[ "$TEST_MODE" = "live" ]]; then
  echo "Skipping live service CI for fork build" >&2
  exit 0
fi

case "$1" in
  after_failure)
    if [[ -n "${TRAVIS_TAG}" ]]; then
      echo "Skipping $1 for release" >&2
      exit 0
    fi

    make logs
    ;;

  after_script)
    if [[ -n "${TRAVIS_TAG}" ]]; then
      echo "Skipping $1 for release" >&2
      exit 0
    fi

    make clean-storage stop
    ;;

  after_success)
    if [[ -n "${TRAVIS_TAG}" ]]; then
      echo "Skipping $1 for release" >&2
      exit 0
    fi

    if [[ "$TEST_MODE" = "local" ]]; then
      bash <(curl -s https://codecov.io/bash)
    fi
    ;;

  before_deploy)
    echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin
    make release
    ;;

  before_install)
    sudo curl -fsSL "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose version
    ;;

  deploy)
    make deploy
    ;;

  install)
    if [[ -n "${TRAVIS_TAG}" ]]; then
      echo "Skipping $1 for release" >&2
      exit 0
    fi

    make build verify-build
    ;;

  script)
    if [[ -n "${TRAVIS_TAG}" ]]; then
      echo "Skipping $1 for release" >&2
      exit 0
    fi

    if [[ "$TRAVIS_EVENT_TYPE" = "cron" ]]; then
      make renew-cert
      exit 0
    fi

    make start
    make integration-tests
    ;;

  *)
    echo "Unrecognized command: $1" >&2
    exit 1
    ;;
esac
