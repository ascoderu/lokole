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
compose_env_file='.env'
secrets_env_file='secrets.env'
ssh_key_file='id_rsa'
pypirc_file="$HOME/.pypirc"

openssl aes-256-cbc -K "$encrypted_2ff31a343d6c_key" -iv "$encrypted_2ff31a343d6c_iv" -in travis/secrets.tar.enc -out "$secrets_archive" -d
tar xf "$secrets_archive" -C . "$ssh_key_file" "$secrets_env_file"

cleanup() {
  rm -f "$compose_env_file" "$secrets_archive" "$ssh_key_file" "$pypirc_file" "$secrets_env_file"
}
trap cleanup EXIT

cat > "$compose_env_file" << EOF
APP_PORT=80
BUILD_TAG=${TRAVIS_TAG}
ENV_FILE=${secrets_env_file}
EOF

docker-compose build

docker login --username="$DOCKER_USERNAME" --password="$DOCKER_PASSWORD"
docker-compose push

cat > "$pypirc_file" << EOF
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

while ! ${python} setup.py sdist upload; do
  echo "Unable to upload to PyPI, retrying" >&2
  sleep 1m
done

if [ -z "$VM_HOST" ] || [ -z "$VM_USER" ]; then
  echo "No deployment target, skipping upgrade of application" >&2; exit 0
fi

if [ ! -f "$ssh_key_file" ] || [ ! -f "$secrets_env_file" ]; then
  echo "No deployment secrets found, unable to upgrade application" >&2; exit 2
fi

scp -i "$ssh_key_file" -o "StrictHostKeyChecking no" \
  "$compose_env_file" \
  "$secrets_env_file" \
  'docker-compose.yml' \
  'setup/systemd_start.sh' \
  'setup/systemd_stop.sh' \
  "$VM_USER@$VM_HOST":~/opwen_cloudserver

ssh -i "$ssh_key_file" -o "StrictHostKeyChecking no" \
  "$VM_USER@$VM_HOST" \
  'sudo systemctl restart opwen_cloudserver'

echo "All done with deployment" >&2; exit 0
