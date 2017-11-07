FROM alpine:3.6

ADD opwen_email_server /app/opwen_email_server
ADD runjob.py /app/job.py
ADD requirements.txt /app/requirements.txt

ARG BUILD_DEPENDENCIES="build-base python3-dev"
RUN apk add --no-cache ${BUILD_DEPENDENCIES} python3 libstdc++ libffi-dev openssl-dev \
  && python3 -m ensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install -U --no-cache-dir -q pip setuptools \
  && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip; fi \
  && pip3 --no-cache-dir -q install -r /app/requirements.txt \
  && apk del ${BUILD_DEPENDENCIES}

ENV JOB_NAME="SET_ME"

WORKDIR /app
CMD "/app/job.py" "$JOB_NAME"
