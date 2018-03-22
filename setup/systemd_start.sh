#!/usr/bin/env bash

pushd "$(dirname "$0")"

docker-compose pull
docker-compose up -d

popd
