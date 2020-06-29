#!/usr/bin/env bash

declare -a api_spec_paths

case "${CONNEXION_SPEC}" in
  file:*)
    specs="${CONNEXION_SPEC:5}"
    IFS="," read -r -a api_spec_paths <<<"${specs}"
    ;;
  dir:*)
    specs="${CONNEXION_SPEC:4}"
    mapfile -t api_spec_paths < <(find "${specs}" -type f -name '*.yaml')
    ;;
esac

apis=""
for api_spec_path in "${api_spec_paths[@]}"; do
  if [[ ! -f "${api_spec_path}" ]]; then
    echo "Unable to start server: connexion spec file ${api_spec_path} does not exist" >&2
    exit 1
  fi
  apis="${apis},'${api_spec_path}'"
done
apis="[${apis:1:${#apis}-1}]"

if [[ "${LOKOLE_STORAGE_PROVIDER}" = "LOCAL" ]]; then
  mkdir -p "${LOKOLE_EMAIL_SERVER_AZURE_BLOBS_NAME}"
  mkdir -p "${LOKOLE_EMAIL_SERVER_AZURE_TABLES_NAME}"
  mkdir -p "${LOKOLE_CLIENT_AZURE_STORAGE_NAME}"
fi

exec gunicorn \
  --workers="${SERVER_WORKERS}" \
  --log-level="${LOKOLE_LOG_LEVEL}" \
  --bind="0.0.0.0:${PORT}" \
  "opwen_email_server.integration.wsgi:build_app(apis=${apis}, ui=${TESTING_UI})"
