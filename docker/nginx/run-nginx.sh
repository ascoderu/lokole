#!/usr/bin/env bash

mo /app/nginx.conf.mu > /app/nginx.conf

nginx -c "/app/nginx.conf" -p "${PWD}" -g "daemon off;"
