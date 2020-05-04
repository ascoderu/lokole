#!/usr/bin/env bash

set -e

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

  lint_shell
  lint_docker
  lint_yaml
  lint_helm
)
