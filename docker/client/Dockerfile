ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION} AS builder

ARG NODE_VERSION=12.x
ARG YARN_VERSION=1.22.4
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}" | bash \
 && curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
 && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
 && apt-get install -y --no-install-recommends nodejs=12.16.2-1nodesource1 mobile-broadband-provider-info=20170903-1 \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g "yarn@${YARN_VERSION}"

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install

COPY requirements-webapp.txt ./
RUN pip install --no-cache-dir -r requirements-webapp.txt

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN yarn run lint \
 && yarn run build

ENV OPWEN_SESSION_KEY=changeme
ENV OPWEN_SETTINGS=/app/docker/client/client.env

CMD ["python", "/app/manage.py", "devserver"]

FROM builder AS compiler

ARG VERSION=0.0.0

RUN pybabel extract -F babel.cfg -k lazy_gettext -o babel.pot opwen_email_client/webapp \
 && pybabel compile -d opwen_email_client/webapp/translations

RUN sed -i "s|^__version__ = '[^']*'|__version__ = '${VERSION}'|g" opwen_email_client/__init__.py \
 && sed -i "s|^__version__ = '[^']*'|__version__ = '${VERSION}'|g" opwen_email_server/__init__.py \
 && python setup.py sdist \
 && cp "dist/opwen_email_client-${VERSION}.tar.gz" dist/pkg.tar.gz

FROM python:${PYTHON_VERSION}-slim AS runtime

# hadolint ignore=DL3010
COPY --from=compiler /app/dist/pkg.tar.gz /app/dist/pkg.tar.gz

# hadolint ignore=DL3013
RUN pip install --no-cache-dir "/app/dist/pkg.tar.gz[opwen_email_server]" \
 && rm -rf /tmp/pip-ephem-wheel-cache*

COPY --from=compiler /app/docker/client/run-gunicorn.sh /app/run-gunicorn.sh
COPY --from=compiler /app/docker/client/client.env /app/client.env

ENV OPWEN_SESSION_KEY=changeme
ENV OPWEN_SETTINGS=/app/client.env

CMD ["/app/run-gunicorn.sh"]
