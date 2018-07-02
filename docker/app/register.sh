#!/usr/bin/env bash

setup_failed() { echo "$1" >&2; exit 1; }
random_string() { < /dev/urandom tr -dc '_A-Z-a-z-0-9' | head -c32; }

opwen_client_domain="${OPWEN_CLIENT_NAME}.${OPWEN_ROOT_DOMAIN}"
opwen_client_id="$(random_string)"

#
# check if the client name is available
#

curl \
  --silent \
  --fail \
  --output /dev/null \
  --header "Authorization: Bearer ${SENDGRID_KEY}" \
  "https://api.sendgrid.com/v3/user/webhooks/parse/settings/${opwen_client_domain}" \
&& setup_failed "Client ${opwen_client_domain} already exists"

#
# register the client with the email service
#

registration_virtualenv="$(mktemp -d /tmp/opwen_email_server.XXXXXX)"

python3 -m venv "${registration_virtualenv}"
while ! "${registration_virtualenv}/bin/pip" install --no-cache-dir -U pip setuptools; do sleep 20s; done
while ! "${registration_virtualenv}/bin/pip" install --no-cache-dir opwen_email_server; do sleep 20s; done

"${registration_virtualenv}/bin/registerclient.py" \
  --tables_account="${REGISTRATION_SERVER_TABLES_ACCOUNT_NAME}" \
  --tables_key="${REGISTRATION_SERVER_TABLES_ACCOUNT_KEY}" \
  --client_account="${OPWEN_REMOTE_ACCOUNT_NAME}" \
  --client_key="${OPWEN_REMOTE_ACCOUNT_KEY}" \
  --client="${opwen_client_id}" \
  --domain="${opwen_client_domain}" \
|| setup_failed "Unable to register with email server"

rm -rf "${registration_virtualenv}"

#
# register the client with sendgrid
#

curl \
  --fail \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${SENDGRID_KEY}" \
  --data "{\"hostname\":\"${opwen_client_domain}\",\"url\":\"http://${OPWEN_EMAIL_SERVER_INBOX_API}/api/email/sendgrid/${opwen_client_id}\",\"spam_check\":true,\"send_raw\":true}" \
  'https://api.sendgrid.com/v3/user/webhooks/parse/settings' \
|| setup_failed "Unable to register with sendgrid"

#
# register the client with cloudflare
#

curl \
  --fail \
  --header "Content-Type: application/json" \
  --header "X-Auth-Key: ${CLOUDFLARE_KEY}" \
  --header "X-Auth-Email: ${CLOUDFLARE_USER}" \
  --data "{\"type\":\"MX\",\"name\":\"${OPWEN_CLIENT_NAME}\",\"content\":\"mx.sendgrid.net\",\"proxied\":false,\"priority\":1}" \
  "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE}/dns_records" \
|| setup_failed "Unable to register with cloudflare"

#
# save environment variables
#

mkdir -p /envs/prod
printf "/state" > /envs/prod/OPWEN_STATE_DIRECTORY
random_string > /envs/prod/OPWEN_ADMIN_SECRET
random_string > /envs/prod/OPWEN_SESSION_KEY
random_string > /envs/prod/OPWEN_PASSWORD_SALT
printf "${OPWEN_EMAIL_SERVER_READ_API}" > /envs/prod/OPWEN_EMAIL_SERVER_READ_API
printf "${OPWEN_EMAIL_SERVER_WRITE_API}" > /envs/prod/OPWEN_EMAIL_SERVER_WRITE_API
printf "${OPWEN_ROOT_DOMAIN}" > /envs/prod/OPWEN_ROOT_DOMAIN
printf "${OPWEN_REMOTE_ACCOUNT_NAME}" > /envs/prod/OPWEN_REMOTE_ACCOUNT_NAME
printf "${OPWEN_REMOTE_ACCOUNT_KEY}" > /envs/prod/OPWEN_REMOTE_ACCOUNT_KEY
printf "${OPWEN_CLIENT_NAME}" > /envs/prod/OPWEN_CLIENT_NAME
printf "${opwen_client_id}" > /envs/prod/OPWEN_CLIENT_ID
