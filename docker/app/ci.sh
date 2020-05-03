#!/usr/bin/env bash

set -e

tests() {
  LOKOLE_LOG_LEVEL=CRITICAL \
  coverage run -m nose2 -v && \
  coverage xml && \
  coverage report
}

lint_swagger() {
  find opwen_email_server/swagger -type f -name '*.yaml' | while read -r file; do
    echo "==================== ${file} ===================="
    swagger-flex --source="${file}" || exit 1
  done
}

lint_python() {
  flake8 opwen_email_server opwen_email_client
  isort --check-only --recursive opwen_email_server opwen_email_client
  yapf --recursive --parallel --diff opwen_email_server opwen_email_client tests
  bandit --recursive opwen_email_server opwen_email_client
  mypy opwen_email_server opwen_email_client
}

lint_yaml() {
  find . -type f -regex '.*\.ya?ml' | grep -v '^./helm/' | while read -r file; do
    echo "==================== ${file} ===================="
    yamllint "${file}" || exit 1
  done
}

lint_docker() {
  if command -v hadolint >/dev/null; then
    find . -type f -name Dockerfile | while read -r file; do
      echo "==================== ${file} ===================="
      hadolint "${file}" || exit 1
    done
  fi
}

lint_shell() {
  if command -v shellcheck >/dev/null; then
    find . -type f -name '*.sh' | while read -r file; do
      echo "==================== ${file} ===================="
      shellcheck "${file}" || exit 1
    done
  fi
}

lint_helm() {
  helm lint --strict ./helm/opwen_cloudserver
  helm template ./helm/opwen_cloudserver > helm.yaml && kubeval --ignore-missing-schemas helm.yaml && rm helm.yaml
}

scriptdir="$(dirname "$0")"

(
  cd "${scriptdir}/../.."

  export PYTHONDONTWRITEBYTECODE=1
  lint_python
  lint_shell
  lint_swagger
  lint_docker
  lint_yaml
  lint_helm
  tests
)
