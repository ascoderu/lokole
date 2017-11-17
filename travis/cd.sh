#!/usr/bin/env bash

set -eo pipefail

if [ -z "$TRAVIS_TAG" ]; then
  echo "Build is not a release, skipping CD" >&2; exit 0
fi

if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
  echo "No docker credentials configured, unable to publish builds" >&2; exit 1
fi

if [ -z "$PYPI_USERNAME" ] || [ -z "$PYPI_PASSWORD" ]; then
  echo "No PyPI credentials configured, unable to publish builds" >&2; exit 1
fi

secrets_archive="$(mktemp)"
compose_file="$(mktemp)"
env_file='.env'
cert_file='cert.pem'

openssl aes-256-cbc -K "$encrypted_2ff31a343d6c_key" -iv "$encrypted_2ff31a343d6c_iv" -in travis/secrets.tar.enc -out "$secrets_archive" -d
tar xf "$secrets_archive" -C . "$cert_file" "$env_file"
touch "$env_file"

cleanup() {
  rm -f "$compose_file" "$env_file" "$secrets_archive" "$cert_file" "$HOME/.pypirc"
}
trap cleanup EXIT

APP_PORT="80" BUILD_TAG="$TRAVIS_TAG" ENV_FILE="$env_file" \
  docker-compose config > "$compose_file"

docker-compose -f "$compose_file" build

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"
docker-compose -f "$compose_file" push

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

${python} setup.py sdist upload

if [ -z "$SERVICE_FABRIC_HOST" ] || [ -z "$SERVICE_FABRIC_DEPLOYMENT_NAME" ]; then
  echo "No service fabric credentials configured, skipping upgrade of cluster" >&2; exit 0
fi

if [ ! -f "$cert_file" ] || [ ! -s "$env_file" ]; then
  echo "No service fabric secrets found, unable to upgrade cluster" >&2; exit 2
fi

pip="$py_env/bin/pip"
sfctl="$py_env/bin/sfctl"

${pip} install sfctl

REQUESTS_CA_BUNDLE="$cert_file" ${sfctl} cluster select --endpoint "https://$SERVICE_FABRIC_HOST:19080" --pem "$cert_file" --no-verify
sfctl compose upgrade --deployment-name "$SERVICE_FABRIC_DEPLOYMENT_NAME" --file-path "$compose_file"

echo "All done with deployment" >&2; exit 0
