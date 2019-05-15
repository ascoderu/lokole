FROM nginx:stable

COPY docker/nginx/static /static
COPY docker/nginx/nginx.conf.template /app/nginx.conf.template
COPY docker/nginx/run-nginx.sh /app/run-nginx.sh

RUN mkdir -p /var/cache/nginx \
  && rm /etc/nginx/conf.d/default.conf \
  && chown -R nginx:nginx \
    /app \
    /static \
    /var/cache/nginx

ENV DNS_RESOLVER=""
ENV HOSTNAME_EMAIL_RECEIVE="SET_ME"
ENV HOSTNAME_CLIENT_METRICS="SET_ME"
ENV HOSTNAME_CLIENT_WRITE="SET_ME"
ENV HOSTNAME_CLIENT_READ="SET_ME"
ENV HOSTNAME_CLIENT_REGISTER="SET_ME"
ENV PORT=8888

EXPOSE ${PORT}
USER nginx
WORKDIR /static

CMD ["/app/run-nginx.sh"]
