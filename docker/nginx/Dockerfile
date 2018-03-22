FROM nginx:stable

ADD opwen_email_server/static/favicon.ico /static/favicon.ico
ADD opwen_email_server/static/robots.txt /static/robots.txt
ADD docker/nginx/nginx.conf /etc/nginx/conf.d/frontend.conf

RUN rm /etc/nginx/conf.d/default.conf

RUN apt-get update \
  && apt-get install -y curl \
  && rm -rf /var/lib/apt/lists/*

ADD docker/nginx/healthcheck.sh /app/healthcheck.sh
HEALTHCHECK --interval=89s --timeout=17s CMD /app/healthcheck.sh
