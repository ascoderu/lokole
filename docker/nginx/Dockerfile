FROM nginx:stable

RUN apt-get -qq update \
  && apt-get -qq install -y --no-install-recommends \
    ca-certificates=20161130+nmu1+deb9u1 \
    curl=7.52.1-5+deb9u9 \
    apache2-utils=2.4.25-3+deb9u6 \
  && curl -fsSL https://git.io/get-mo -o /usr/local/bin/mo \
  && chmod +x /usr/local/bin/mo \
  && rm -rf /var/lib/apt/lists/* \
  && rm /etc/nginx/conf.d/default.conf

COPY docker/nginx/static /static
COPY docker/nginx/nginx.conf.mu /app/frontend.conf.mu
COPY docker/nginx/run-nginx.sh /app/run-nginx.sh

ENV DNS_RESOLVER=""
ENV HOSTNAME_EMAIL_RECEIVE="SET_ME"
ENV HOSTNAME_CLIENT_WRITE="SET_ME"
ENV HOSTNAME_CLIENT_READ="SET_ME"
ENV HOSTNAME_CLIENT_REGISTER="SET_ME"
ENV REGISTRATION_USERNAME="SET_ME"
ENV REGISTRATION_PASSWORD="SET_ME"

COPY docker/nginx/healthcheck.sh /app/healthcheck.sh
HEALTHCHECK --interval=89s --timeout=17s CMD /app/healthcheck.sh
CMD ["/app/run-nginx.sh"]
