#!/usr/bin/env bash

mo < /app/nginx.conf.template > /app/nginx.conf

nginx -c "/app/nginx.conf" -p "${PWD}" -g "daemon off;"
