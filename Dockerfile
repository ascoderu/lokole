FROM alpine:3.6

ADD opwen_email_server /app/opwen_email_server
ADD runserver.py /app/server.py
ADD requirements.txt /app/requirements.txt
ADD opwen_email_server/static/email-api-spec.yaml /app/swagger1.yaml
ADD opwen_email_server/static/healthcheck-spec.yaml /app/swagger2.yaml

ARG BUILD_DEPENDENCIES="build-base python3-dev"
RUN apk add --no-cache ${BUILD_DEPENDENCIES} python3 libstdc++ libffi-dev openssl-dev \
  && python3 -m ensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install -U --no-cache-dir -q pip setuptools \
  && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip; fi \
  && pip3 --no-cache-dir -q install -r /app/requirements.txt \
  && pip3 --no-cache-dir -q install gunicorn==19.7.1 tornado==4.5.2 \
  && apk del ${BUILD_DEPENDENCIES}

EXPOSE 80
WORKDIR /app
CMD ["gunicorn", "-w", "8", "-b", "0.0.0.0:80", \
     "server:build_app(apis=['/app/swagger1.yaml', '/app/swagger2.yaml'], server='tornado')"]
