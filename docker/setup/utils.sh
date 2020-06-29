#!/usr/bin/env bash

usage() {
  local script="$1"
  local usage

  usage="$(grep '^##' "${script}" | sed 's/^##//')"

  printf "Usage: %s\n\n%s\n" "${script}" "${usage}"
}

log() {
  local message="$1"
  local format="\033[1m\033[7m"
  local reset="\033[0m"

  echo -e "$(date)\t${format}${message}${reset}"
}

required_env() {
  local scriptname="$1"
  local envname="$2"

  if [[ -z "${!envname}" ]]; then
    echo "${envname} must be set" >&2
    usage "${scriptname}"
    exit 1
  fi
}

required_file() {
  local scriptname="$1"
  local filename="$2"

  if [[ ! -f "${filename}" ]]; then
    echo "${filename} must exist" >&2
    usage "${scriptname}"
    exit 1
  fi
}

generate_identifier() {
  local length="$1"

  tr </dev/urandom -dc 'a-z0-9' | head -c"${length}"
}

get_dotenv() {
  local dotenvfile="$1"
  local variable="$2"

  grep "${variable}" "${dotenvfile}" | cut -d'=' -f2- | tr -d '\r'
}

use_resource_group() {
  local name="$1"

  if [[ "$(az group exists --name "${name}")" = "false" ]]; then
    log "Creating resource group ${name}"

    az group create --name "${name}"

    az group wait \
      --name "${name}" \
      --exists
  else
    log "Using existing resource group ${name}"
  fi

  az configure --defaults group="${name}"
}

helm_init() {
  helm init --history-max 200 --node-selectors "beta.kubernetes.io/os=linux" --wait
}
