ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION} AS builder

RUN curl -sSL https://git.io/get-mo -o /usr/bin/mo \
  && chmod +x /usr/bin/mo

FROM nginx:stable

COPY --from=builder /usr/bin/mo /usr/bin/mo
COPY docker/nginx/static /static
COPY docker/nginx/*.mustache /app/
COPY docker/nginx/run-nginx.sh /app/run-nginx.sh

RUN mkdir -p /var/cache/nginx /etc/nginx/modules-enabled /etc/nginx/sites-enabled \
  && rm /etc/nginx/conf.d/default.conf \
  && chown -R www-data:www-data \
    /app \
    /static \
    /run \
    /etc/nginx/modules-enabled \
    /etc/nginx/sites-enabled \
    /var/cache/nginx

ENV DNS_RESOLVER=""
ENV HOSTNAME_WEBAPP="SET_ME"
ENV HOSTNAME_EMAIL_RECEIVE="SET_ME"
ENV HOSTNAME_CLIENT_METRICS="SET_ME"
ENV HOSTNAME_CLIENT_WRITE="SET_ME"
ENV HOSTNAME_CLIENT_READ="SET_ME"
ENV HOSTNAME_CLIENT_REGISTER="SET_ME"
ENV PORT=8888

EXPOSE ${PORT}
USER www-data
WORKDIR /static

CMD ["/app/run-nginx.sh"]
