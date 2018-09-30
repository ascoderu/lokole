FROM nginx:stable

RUN apt-get -qq update \
  && apt-get -qq install -y curl \
  && curl -fsSL https://git.io/get-mo -o /usr/local/bin/mo \
  && chmod +x /usr/local/bin/mo \
  && rm -rf /var/lib/apt/lists/*

ADD opwen_email_server/static/favicon.ico /static/favicon.ico
ADD opwen_email_server/static/robots.txt /static/robots.txt
ADD docker/nginx/nginx.conf.mu /app/frontend.conf.mu
ADD docker/nginx/run-nginx.sh /app/run-nginx.sh

RUN rm /etc/nginx/conf.d/default.conf

ENV DNS_RESOLVER=""
ENV HOSTNAME_EMAIL_RECEIVE="apiemailreceive"
ENV HOSTNAME_CLIENT_WRITE="apiclientwrite"
ENV HOSTNAME_CLIENT_READ="apiclientread"

ADD docker/nginx/healthcheck.sh /app/healthcheck.sh
HEALTHCHECK --interval=89s --timeout=17s CMD /app/healthcheck.sh
CMD ["/app/run-nginx.sh"]
