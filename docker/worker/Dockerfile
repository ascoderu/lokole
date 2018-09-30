FROM python:3.6

ADD requirements.txt /app/requirements.txt
ADD requirements-prod.txt /app/requirements-prod.txt
RUN apt-get update \
  && apt-get install -y libffi-dev libssl-dev ca-certificates curl \
  && python3 -m venv /venv \
  && /venv/bin/pip3 --no-cache-dir -q install -U pip setuptools \
  && /venv/bin/pip3 --no-cache-dir -q install -r /app/requirements.txt \
  && /venv/bin/pip3 --no-cache-dir -q install -r /app/requirements-prod.txt \
  && rm -rf /var/lib/apt/lists/*

ADD opwen_email_server /app/opwen_email_server
ADD docker/worker/run-celery.sh /app/run-celery.sh
ADD docker/docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /app
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/app/run-celery.sh"]
