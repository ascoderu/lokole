FROM nginx:alpine

ADD opwen_email_server/static/favicon.ico /static/favicon.ico
ADD opwen_email_server/static/robots.txt /static/robots.txt
ADD docker/nginx/nginx.conf /etc/nginx/conf.d/frontend.conf

RUN rm /etc/nginx/conf.d/default.conf

RUN apk update && apk add --no-cache curl

ADD docker/nginx/healthcheck.sh /app/healthcheck.sh
HEALTHCHECK --interval=90s --timeout=15s CMD /app/healthcheck.sh
