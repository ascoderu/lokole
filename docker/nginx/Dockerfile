FROM nginx:stable AS builder

RUN apt-get -qq update \
  && apt-get -qq install -y --no-install-recommends \
    ca-certificates=20161130+nmu1+deb9u1 \
    curl=7.52.1-5+deb9u9 \
  && rm -rf /var/lib/apt/lists/* \
  && curl -fsSL https://git.io/get-mo -o /usr/local/bin/mo \
  && chmod +x /usr/local/bin/mo

FROM nginx:stable AS runtime

COPY --from=builder /usr/local/bin/mo /usr/local/bin/mo
COPY docker/nginx/static /static
COPY docker/nginx/nginx.conf.mu /app/nginx.conf.mu
COPY docker/nginx/run-nginx.sh /app/run-nginx.sh

RUN mkdir -p /var/cache/nginx \
  && rm /etc/nginx/conf.d/default.conf \
  && chown -R nginx:nginx \
    /app \
    /static \
    /var/cache/nginx

ENV DNS_RESOLVER=""
ENV HOSTNAME_EMAIL_RECEIVE="SET_ME"
ENV HOSTNAME_CLIENT_WRITE="SET_ME"
ENV HOSTNAME_CLIENT_READ="SET_ME"
ENV HOSTNAME_CLIENT_REGISTER="SET_ME"
ENV PORT=8888

EXPOSE ${PORT}
USER nginx
WORKDIR /static

CMD ["/app/run-nginx.sh"]
