#!/usr/bin/env bash

declare -a api_spec_paths
api_spec_paths=(${CONNEXION_SPEC//,/ })

apis=""
for api_spec_path in "${api_spec_paths[@]}"; do
  if [ ! -f "${api_spec_path}" ]; then
    echo "Unable to start server: connexion spec file ${api_spec_path} does not exist" >&2
    exit 1
  fi
  apis="${apis},'${api_spec_path}'"
done
apis="[${apis:1:${#apis}-1}]"

"${PY_ENV}/bin/gunicorn" \
  --workers="${GUNICORN_WORKERS}" \
  --log-level="${LOKOLE_LOG_LEVEL}" \
  --bind="0.0.0.0:${PORT}" \
  "runserver:build_app(apis=${apis}, server='${CONNEXION_SERVER}', ui=${TESTING_UI})"
