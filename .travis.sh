#!/usr/bin/env bash

set -eo pipefail

if [[ "$TRAVIS_PULL_REQUEST" = "false" ]] && [[ "$TEST_MODE" = "live" ]]; then
  echo "Skipping live service CI for branch build" >&2
  exit 0
fi

if [[ "$TRAVIS_PULL_REQUEST_SLUG" != "ascoderu/opwen-cloudserver" ]] && [[ "$TEST_MODE" = "live" ]]; then
  echo "Skipping live service CI for fork build" >&2
  exit 0
fi

case "$1" in
  after_failure)
    docker-compose ps
    ALL=true make logs
    ;;

  after_script)
    make stop
    ;;

  after_success)
    if [[ "$TEST_MODE" = "local" ]]; then
      bash <(curl -s https://codecov.io/bash)
    fi
    ;;

  before_deploy)
    echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USERNAME" --password-stdin
    ;;

  before_install)
    sudo curl -fsSL "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose version
    ;;

  deploy)
    if [[ "$TEST_MODE" = "local" ]]; then
      DOCKER_TAG="$TRAVIS_TAG" make release deploy
    fi
    ;;

  install)
    export BUILD_TARGET=runtime
    make build verify-build
    ;;

  script)
    if [[ "$TRAVIS_EVENT_TYPE" = "cron" ]]; then
      make renew-cert
      exit 0
    fi

    if [[ "$TEST_MODE" = "live" ]]; then
      export REGISTRATION_CREDENTIALS="$GITHUB_AUTH_USERNAME:$GITHUB_AUTH_TOKEN"
      export LOKOLE_QUEUE_BROKER_SCHEME="azureservicebus"
    else
      export REGISTRATION_CREDENTIALS="admin:password"
      export LOKOLE_QUEUE_BROKER_SCHEME="amqp"
    fi

    export CI=true
    make start
    make integration-tests
    ;;

  *)
    echo "Unrecognized command: $1" >&2
    exit 1
    ;;
esac
