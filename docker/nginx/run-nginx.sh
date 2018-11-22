#!/usr/bin/env bash

mo /app/frontend.conf.mu > /etc/nginx/conf.d/frontend.conf

htpasswd -bc "/etc/nginx/.htpasswd" "${REGISTRATION_USERNAME}" "${REGISTRATION_PASSWORD}"

nginx -g "daemon off;"
