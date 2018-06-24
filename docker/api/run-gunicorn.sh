#!/usr/bin/env sh

api_spec="/app/${CONNEXION_SPEC}"
healthcheck_spec="/app/opwen_email_server/static/healthcheck-spec.yaml"

for spec in "${api_spec}" "${healthcheck_spec}"; do
  if [ ! -f "${spec}" ]; then
    echo "Unable to start server: connexion spec file ${spec} does not exist" >&2
    exit 1
  fi
done

gunicorn \
  --workers="${GUNICORN_WORKERS}" \
  --bind="0.0.0.0:80" \
  "server:build_app(apis=['${api_spec}','${healthcheck_spec}'], server='tornado')"
