#!/usr/bin/env bash

settings_path="$1" && shift

compgen -e | grep -E "^(OPWEN)|(LOKOLE)" | while read -r key; do
  other_settings="$(grep -v "^${key}=" "${settings_path}")"
  echo -e "${other_settings}\n${key}=${!key}" > "${settings_path}"
done

exec "$@"
