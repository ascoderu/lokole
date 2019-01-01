FROM python:3.6

ARG CLIENT_VERSION=

ADD requirements.txt /app/requirements.txt
RUN python3 -m venv /venv \
  && /venv/bin/pip install --no-cache-dir -U pip setuptools \
  && /venv/bin/pip install --no-cache-dir -r /app/requirements.txt \
  && /venv/bin/pip install --no-cache-dir opwen_email_client==${CLIENT_VERSION} \
  && /venv/bin/pybabel compile -d /venv/lib/python3.6/site-packages/opwen_email_client/webapp/translations \
  && apt-get -qq update \
  && apt-get -qq install -y curl nginx supervisor \
  && rm -rf /var/lib/apt/lists/* \
  && rm /etc/nginx/sites-enabled/default

ARG CLOUDFLARE_KEY=
ARG CLOUDFLARE_USER=
ARG CLOUDFLARE_ZONE=
ARG SENDGRID_KEY=
ARG REGISTRATION_SERVER_TABLES_ACCOUNT_KEY=
ARG REGISTRATION_SERVER_TABLES_ACCOUNT_NAME=
ARG OPWEN_CLIENT_NAME=
ARG OPWEN_REMOTE_ACCOUNT_KEY=
ARG OPWEN_REMOTE_ACCOUNT_NAME=
ARG OPWEN_ROOT_DOMAIN=lokole.ca
ARG OPWEN_EMAIL_SERVER_HOSTNAME=mailserver.lokole.ca

ADD register.sh /app/register.sh
RUN /app/register.sh \
  && mkdir -p /state

ADD supervisor.conf /app/supervisor.conf
ADD cron.py /app/cron.py
ADD nginx.conf /etc/nginx/conf.d/frontend.conf

ENV OPWEN_SYNC_SCHEDULE=
ENV OPWEN_WEBAPP_TIMEOUT_SECONDS=30
ENV OPWEN_WEBAPP_WORKERS=2

EXPOSE 80
CMD ["/usr/bin/supervisord", "-c", "/app/supervisor.conf"]
