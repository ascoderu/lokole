FROM python:3.6

ENV PY_ENV="/venv"
ADD requirements.txt /app/requirements.txt
ADD requirements-prod.txt /app/requirements-prod.txt
RUN apt-get update \
  && apt-get install -y libffi-dev libssl-dev ca-certificates curl \
  && python3 -m venv "${PY_ENV}" \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -U pip setuptools \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements.txt \
  && "${PY_ENV}/bin/pip" --no-cache-dir -q install -r /app/requirements-prod.txt \
  && rm -rf /var/lib/apt/lists/*

ADD opwen_email_server /app/opwen_email_server
ADD runserver.py /app/runserver.py
ADD docker/api/healthcheck.sh /app/healthcheck.sh
ADD docker/api/run-gunicorn.sh /app/run-gunicorn.sh
ADD docker/docker-entrypoint.sh /docker-entrypoint.sh

ENV TESTING_UI="False"
ENV CONNEXION_SERVER="tornado"
ENV CONNEXION_SPEC="SET_ME"
ENV GUNICORN_WORKERS="1"
ENV LOKOLE_LOG_LEVEL="INFO"
ENV PORT="80"

EXPOSE ${PORT}
WORKDIR /app
HEALTHCHECK --interval=59m --timeout=5s CMD /app/healthcheck.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/app/run-gunicorn.sh"]
