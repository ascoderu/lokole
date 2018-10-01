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
ADD runserver.py /app/server.py
ADD docker/api/healthcheck.sh /app/healthcheck.sh
ADD docker/api/run-gunicorn.sh /app/run-gunicorn.sh
ADD docker/docker-entrypoint.sh /docker-entrypoint.sh

ENV TESTING_UI="False"
ENV CONNEXION_SERVER="tornado"
ENV CONNEXION_SPEC="SET_ME"
ENV GUNICORN_WORKERS="1"

EXPOSE 80
WORKDIR /app
HEALTHCHECK --interval=59m --timeout=5s CMD /app/healthcheck.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/app/run-gunicorn.sh"]
