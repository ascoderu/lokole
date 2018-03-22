FROM python:3.6

ENV JOB_NAME="SET_ME"
ENV LOKOLE_QUEUE_ERROR_FILE="/app/queue_health.txt"

ADD opwen_email_server /app/opwen_email_server
ADD requirements.txt /app/requirements.txt
ADD docker/job/healthcheck.sh /app/healthcheck.sh

RUN apt-get update \
  && apt-get install -y libffi-dev libssl-dev ca-certificates \
  && pip3 install -U --no-cache-dir pip setuptools \
  && pip3 --no-cache-dir install -r /app/requirements.txt \
  && touch ${LOKOLE_QUEUE_ERROR_FILE} \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
HEALTHCHECK CMD /app/healthcheck.sh
CMD "python3" "-m" "${JOB_NAME}"
