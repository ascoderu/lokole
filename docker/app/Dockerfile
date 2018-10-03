FROM python:3.6

ENV PY_ENV="/venv"
ADD requirements.txt /app/requirements.txt
RUN apt-get update \
  && apt-get install -y libffi-dev libssl-dev ca-certificates curl \
  && python3 -m venv "${PY_ENV}" \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -U pip setuptools \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements.txt \
  && rm -rf /var/lib/apt/lists/*

ADD requirements-dev.txt /app/requirements-dev.txt
ADD requirements-prod.txt /app/requirements-prod.txt
ARG USE_DEVTOOLS="False"
RUN if [ "${USE_DEVTOOLS}" = "True" ]; then \
      "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements-dev.txt; \
      mkdir -p /data/server-blobs /data/server-tables /data/client-blobs; \
    else \
      "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements-prod.txt; \
    fi

ADD opwen_email_server /app/opwen_email_server
ADD runserver.py /app/runserver.py
ADD docker/app/run-gunicorn.sh /app/run-gunicorn.sh
ADD docker/app/run-celery.sh /app/run-celery.sh
ADD docker/docker-entrypoint.sh /docker-entrypoint.sh

ENV TESTING_UI="False"
ENV CONNEXION_SERVER="tornado"
ENV CONNEXION_SPEC="SET_ME"
ENV GUNICORN_WORKERS="1"
ENV CELERY_WORKERS="1"
ENV LOKOLE_LOG_LEVEL="INFO"
ENV PORT="80"

EXPOSE ${PORT}
WORKDIR /app
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["bash"]
