#!/usr/bin/env bash

mo /app/nginx.conf.mu > /app/nginx.conf

htpasswd -bc "/app/.htpasswd" "${REGISTRATION_USERNAME}" "${REGISTRATION_PASSWORD}"

nginx -c "/app/nginx.conf" -p "${PWD}" -g "daemon off;"
