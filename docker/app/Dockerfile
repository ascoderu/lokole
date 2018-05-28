FROM python:3.6

ARG CLIENT_VERSION=

RUN python3 -m venv /venv \
  && /venv/bin/pip install --no-cache-dir -U pip setuptools \
  && /venv/bin/pip install --no-cache-dir opwen_email_client==${CLIENT_VERSION} \
  && /venv/bin/pybabel compile -d /venv/lib/python3.6/site-packages/opwen_email_client/webapp/translations \
  && apt-get -qq update \
  && apt-get -qq install -y curl nginx \
  && rm -rf /var/lib/apt/lists/* \
  && rm /etc/nginx/sites-enabled/default

ADD run-app.sh /run-app.sh
ADD nginx.conf /etc/nginx/conf.d/frontend.conf

ENV OPWEN_STATE_DIRECTORY=/state
ENV OPWEN_SESSION_KEY=
ENV OPWEN_PASSWORD_SALT=
ENV OPWEN_ADMIN_SECRET=
ENV OPWEN_REMOTE_ACCOUNT_NAME=
ENV OPWEN_REMOTE_ACCOUNT_KEY=
ENV OPWEN_SERVER_TABLES_ACCOUNT_NAME=
ENV OPWEN_SERVER_TABLES_ACCOUNT_KEY=
ENV OPWEN_CLOUDFLARE_ZONE=
ENV OPWEN_CLOUDFLARE_USER=
ENV OPWEN_CLOUDFLARE_KEY=
ENV OPWEN_SENDGRID_KEY=
ENV OPWEN_CLIENT_ID=
ENV OPWEN_CLIENT_NAME=
ENV OPWEN_ROOT_DOMAIN=lokole.ca
ENV OPWEN_EMAIL_SERVER_READ_API=api.mailserver.read.lokole.ca
ENV OPWEN_EMAIL_SERVER_WRITE_API=api.mailserver.write.lokole.ca
ENV OPWEN_EMAIL_SERVER_INBOX_API=api.mailserver.inbox.lokole.ca
ENV OPWEN_WEBAPP_TIMEOUT_SECONDS=30
ENV OPWEN_WEBAPP_WORKERS=2

EXPOSE 80
CMD nginx && /run-app.sh
