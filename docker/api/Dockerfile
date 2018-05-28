FROM python:3.6

ENV API_NAME="SET_ME"
ENV GUNICORN_WORKERS="1"

ADD requirements.txt /app/requirements.txt
RUN apt-get update \
  && apt-get install -y libffi-dev libssl-dev ca-certificates curl \
  && pip3 install -U --no-cache-dir pip setuptools \
  && pip3 --no-cache-dir -q install -r /app/requirements.txt \
  && pip3 --no-cache-dir -q install gunicorn==19.7.1 tornado==4.5.2 \
  && rm -rf /var/lib/apt/lists/*

ADD opwen_email_server /app/opwen_email_server
ADD runserver.py /app/server.py
ADD docker/api/healthcheck.sh /app/healthcheck.sh

EXPOSE 80
WORKDIR /app
HEALTHCHECK --interval=59m --timeout=5s CMD /app/healthcheck.sh
CMD "gunicorn" "-w" "${GUNICORN_WORKERS}" "-b" "0.0.0.0:80" "server:build_app(apis=['/app/${API_NAME}', '/app/opwen_email_server/static/healthcheck-spec.yaml'], server='tornado')"
