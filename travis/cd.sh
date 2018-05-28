#!/usr/bin/env bash

set -eo pipefail

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$PYPI_USERNAME" ] || [ -z "$PYPI_PASSWORD" ]; then
  echo "No PyPI credentials configured, unable to publish builds" >&2; exit 1
fi

if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

cleanup() {
  rm -f ~/.pypirc
}
trap cleanup EXIT

cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi

[pypi]
username: $PYPI_USERNAME
password: $PYPI_PASSWORD
EOF

echo "$TRAVIS_TAG" > version.txt

py_env="$HOME/virtualenv/python$TRAVIS_PYTHON_VERSION"
python="$py_env/bin/python"

make prepare-server -e py_env="$py_env" -e NPM="$(which npm)" -e SHELLCHECK="$(which shellcheck)"

while ! ${python} setup.py sdist upload; do
  echo "Unable to upload to PyPI, retrying" >&2
  sleep 1m
done

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"

docker build \
  --build-arg "CLIENT_VERSION=$TRAVIS_TAG" \
  --tag "$DOCKER_USERNAME/opwenclient_app:$TRAVIS_TAG" \
  docker/app

docker push "$DOCKER_USERNAME/opwenclient_app:$TRAVIS_TAG"

docker tag "$DOCKER_USERNAME/opwenclient_app:$TRAVIS_TAG" "$DOCKER_USERNAME/opwenclient_app:latest"
docker push "$DOCKER_USERNAME/opwenclient:latest"
