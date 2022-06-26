#!/usr/bin/env bash

set -e

scriptdir="$(dirname "$0")"

export FLASK_APP="opwen_email_client.webapp:app"

if [[ -n "${LOKOLE_ADMIN_NAME}" ]] && [[ -n "${LOKOLE_ADMIN_PASSWORD}" ]]; then
  (
#    cd "${scriptdir}/../.."
    flask manage createadmin "${LOKOLE_ADMIN_NAME}" "${LOKOLE_ADMIN_PASSWORD}"
  )
fi

"${scriptdir}/run-celery.sh" &
celery_pid="$!"

"${scriptdir}/run-crontab.sh" &
crontab_pid="$!"

"${scriptdir}/run-gunicorn.sh" &
gunicorn_pid="$!"

while :; do
  if [[ ! -e "/proc/${celery_pid}" ]]; then
    echo "celery crashed" >&2
    exit 1
  elif [[ ! -e "/proc/${crontab_pid}" ]]; then
    echo "crontab crashed" >&2
    exit 2
  elif [[ ! -e "/proc/${gunicorn_pid}" ]]; then
    echo "gunicorn crashed" >&2
    exit 3
  else
    sleep 10
  fi
done
