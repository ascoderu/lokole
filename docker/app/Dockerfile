FROM python:3.6-slim

ARG USE_DEVTOOLS="False"
ENV PY_ENV="/usr/local"
COPY requirements.txt /app/requirements.txt
COPY requirements-prod.txt /app/requirements-prod.txt
COPY requirements-dev.txt /app/requirements-dev.txt
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    libffi-dev=3.2.1-6 \
    libssl-dev=1.1.0j-1~deb9u1 \
    ca-certificates=20161130+nmu1+deb9u1 \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -U pip setuptools \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements.txt \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements-prod.txt \
  && if [ "${USE_DEVTOOLS}" = "True" ]; then \
      "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements-dev.txt; \
    fi \
  && rm -rf /var/lib/apt/lists/*

COPY opwen_email_server /app/opwen_email_server
COPY docker/app/run-gunicorn.sh /app/run-gunicorn.sh
COPY docker/app/run-celery.sh /app/run-celery.sh
COPY docker/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN groupadd -r opwen \
  && useradd -r -s /bin/false -g opwen opwen \
  && chown -R opwen:opwen /app

USER opwen

ENV TESTING_UI="False"
ENV CONNEXION_SERVER="tornado"
ENV CONNEXION_SPEC="SET_ME"
ENV SERVER_WORKERS="1"
ENV QUEUE_WORKERS="1"
ENV LOKOLE_LOG_LEVEL="INFO"
ENV PORT=8080

EXPOSE ${PORT}
WORKDIR /app
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["bash"]
