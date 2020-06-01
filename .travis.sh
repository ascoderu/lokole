#!/usr/bin/env bash

set -eo pipefail

if [[ -z "${TRAVIS_TAG}" ]]; then
  echo "Skipping CI (only processing releases)" >&2
  exit 0
fi

case "$1" in
  after_failure)
    if [[ -n "${TRAVIS_TAG}" ]]; then
      echo "Skipping $1 for release" >&2
      exit 0
    fi

    make status
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
    git remote add ghp "https://${GITHUB_AUTH_TOKEN}@github.com/ascoderu/lokole.git"
    git config --local user.name "Deployment Bot (from Travis CI)"
    git config --local user.email "deploy@travis-ci.org"
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

    make ci build verify-build
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
