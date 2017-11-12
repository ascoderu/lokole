FROM nginx:alpine

ADD opwen_email_server/static/favicon.ico /static/favicon.ico
ADD opwen_email_server/static/robots.txt /static/robots.txt
ADD docker/nginx/nginx.conf /etc/nginx/conf.d/frontend.conf

RUN rm /etc/nginx/conf.d/default.conf
