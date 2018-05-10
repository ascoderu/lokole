#!/usr/bin/env bash

set -eo pipefail

export OPWEN_CLIENT_DOMAIN="${OPWEN_CLIENT_NAME}.${OPWEN_ROOT_DOMAIN}"

registration_guard="${OPWEN_STATE_DIRECTORY}/registration-complete.txt"

if [ ! -f "${registration_guard}" ]; then
  setup_failed() { rm -f "${registration_guard}"; echo "$1" >&2; exit 1; }

  #
  # check if the client name is available
  #

  curl --fail \
    --header "Authorization: Bearer ${OPWEN_SENDGRID_KEY}" \
    "https://api.sendgrid.com/v3/user/webhooks/parse/settings/${OPWEN_CLIENT_DOMAIN}" \
  && setup_failed "Client ${OPWEN_CLIENT_DOMAIN} already exists"

  #
  # register the client with the email service
  #

  registration_state="$(mktemp /tmp/opwen_registration.XXXXXX.txt)"
  registration_virtualenv="$(mktemp -d /tmp/opwen_email_server.XXXXXX)"

  python3 -m venv "${registration_virtualenv}"
  while ! "${registration_virtualenv}/bin/pip" install --no-cache-dir -U pip setuptools; do sleep 20s; done
  while ! "${registration_virtualenv}/bin/pip" install --no-cache-dir opwen_email_server; do sleep 20s; done

  "${registration_virtualenv}/bin/registerclient.py" \
    --tables_account="${OPWEN_SERVER_TABLES_ACCOUNT_NAME}" \
    --tables_key="${OPWEN_SERVER_TABLES_ACCOUNT_KEY}" \
    --client_account="${OPWEN_REMOTE_ACCOUNT_NAME}" \
    --client_key="${OPWEN_REMOTE_ACCOUNT_KEY}" \
    --client="${OPWEN_CLIENT_ID}" \
    --domain="${OPWEN_CLIENT_DOMAIN}" \
  | tee --append "${registration_state}" || setup_failed "Unable to register with email server"

  rm -rf "${registration_virtualenv}"

  #
  # register the client with sendgrid
  #

  curl --fail \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer ${OPWEN_SENDGRID_KEY}" \
    --data "{\"hostname\":\"${OPWEN_CLIENT_DOMAIN}\",\"url\":\"http://${OPWEN_EMAIL_SERVER_INBOX_API}/api/email/sendgrid/${OPWEN_CLIENT_ID}\",\"spam_check\":true,\"send_raw\":true}" \
    'https://api.sendgrid.com/v3/user/webhooks/parse/settings' \
  | tee --append "${registration_state}" || setup_failed "Unable to register with sendgrid"

  #
  # register the client with cloudflare
  #

  curl --fail \
    --header "Content-Type: application/json" \
    --header "X-Auth-Key: ${OPWEN_CLOUDFLARE_KEY}" \
    --header "X-Auth-Email: ${OPWEN_CLOUDFLARE_USER}" \
    --data "{\"type\":\"MX\",\"name\":\"${OPWEN_CLIENT_NAME}\",\"content\":\"mx.sendgrid.net\",\"proxied\":false,\"priority\":1}" \
    "https://api.cloudflare.com/client/v4/zones/${OPWEN_CLOUDFLARE_ZONE}/dns_records" \
  | tee --append "${registration_state}" || setup_failed "Unable to register with cloudflare"

  mv "${registration_state}" "${registration_guard}"
fi

/venv/bin/gunicorn \
  --timeout="${OPWEN_WEBAPP_TIMEOUT_SECONDS}" \
  --workers="${OPWEN_WEBAPP_WORKERS}" \
  --bind="unix:/tmp/gunicorn.sock" \
  opwen_email_client.webapp:app
