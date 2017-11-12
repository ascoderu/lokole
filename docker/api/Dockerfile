FROM alpine:3.6

ENV API_NAME="SET_ME"
ENV GUNICORN_WORKERS="1"

ADD opwen_email_server /app/opwen_email_server
ADD runserver.py /app/server.py
ADD requirements.txt /app/requirements.txt

ARG BUILD_DEPENDENCIES="build-base python3-dev"
RUN apk add --no-cache ${BUILD_DEPENDENCIES} python3 libstdc++ libffi-dev openssl-dev \
  && python3 -m ensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install -U --no-cache-dir pip setuptools \
  && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip; fi \
  && pip3 --no-cache-dir -q install -r /app/requirements.txt \
  && pip3 --no-cache-dir -q install gunicorn==19.7.1 tornado==4.5.2 \
  && apk del ${BUILD_DEPENDENCIES} \
  && apk add --no-cache curl

EXPOSE 80
WORKDIR /app
HEALTHCHECK --interval=1m --timeout=5s CMD curl --fail --silent http://localhost/healthcheck/ping || exit 1
CMD "gunicorn" "-w" "${GUNICORN_WORKERS}" "-b" "0.0.0.0:80" "server:build_app(apis=['/app/${API_NAME}', '/app/opwen_email_server/static/healthcheck-spec.yaml'], server='tornado')"
