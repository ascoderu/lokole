#!/usr/bin/env bash

pushd "$(dirname "$0")"

docker-compose pull
docker-compose up -d

docker images -q | xargs docker rmi || true

popd
