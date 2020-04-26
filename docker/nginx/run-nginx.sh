#!/usr/bin/env bash

mo < /app/nginx.conf.template > /app/nginx.conf
mo < /app/server.conf.template > /etc/nginx/sites-enabled/server.conf

nginx -c "/app/nginx.conf" -p "${PWD}" -g "daemon off;"
