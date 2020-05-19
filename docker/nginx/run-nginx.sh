#!/usr/bin/env bash

mo </app/nginx.conf.mustache >/app/nginx.conf
mo </app/server.conf.mustache >/etc/nginx/sites-enabled/server.conf

exec nginx -c "/app/nginx.conf" -p "${PWD}" -g "daemon off;"
