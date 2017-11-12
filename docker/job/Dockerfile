FROM alpine:3.6

ENV JOB_NAME="SET_ME"
ENV LOKOLE_QUEUE_ERROR_FILE="/app/queue_health.txt"

ADD opwen_email_server /app/opwen_email_server
ADD requirements.txt /app/requirements.txt

ARG BUILD_DEPENDENCIES="build-base python3-dev"
RUN apk add --no-cache ${BUILD_DEPENDENCIES} python3 libstdc++ libffi-dev openssl-dev \
  && python3 -m ensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install -U --no-cache-dir pip setuptools \
  && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip; fi \
  && pip3 --no-cache-dir install -r /app/requirements.txt \
  && touch ${LOKOLE_QUEUE_ERROR_FILE} \
  && apk del ${BUILD_DEPENDENCIES}

WORKDIR /app
HEALTHCHECK CMD test -s "$LOKOLE_QUEUE_ERROR_FILE" && cat "$LOKOLE_QUEUE_ERROR_FILE" && exit 1
CMD "python3" "-m" "${JOB_NAME}"
