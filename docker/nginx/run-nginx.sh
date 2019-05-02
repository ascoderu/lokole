#!/usr/bin/env bash

envsubst < /app/nginx.conf.template > /app/nginx.conf "$(env | sed -e 's/=.*//' -e 's/^/\$/g')"

nginx -c "/app/nginx.conf" -p "${PWD}" -g "daemon off;"
