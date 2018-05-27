#!/usr/bin/env bash

mo /app/frontend.conf.mu > /etc/nginx/conf.d/frontend.conf

nginx -g "daemon off;"
