ARG NODE_VERSION=12
ARG PYTHON_VERSION=3.7
FROM node:${NODE_VERSION} AS yarn

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install

COPY Gruntfile.js .prettierignore ./
COPY opwen_email_client/webapp/static opwen_email_client/webapp/static
RUN yarn run lint \
 && yarn run build

FROM python:${PYTHON_VERSION} AS builder

WORKDIR /app

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY requirements-webapp.txt ./
RUN pip install --no-cache-dir -r requirements-webapp.txt

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV OPWEN_SESSION_KEY=changeme
ENV OPWEN_SETTINGS=/app/docker/client/webapp.env

COPY --from=yarn /app/opwen_email_client/webapp/static/ /app/opwen_email_client/webapp/static/
COPY . .

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

COPY --from=compiler /app/docker/client/run-*.sh /app/docker/client/
COPY --from=compiler /app/docker/client/*.env /app/docker/client/
COPY --from=compiler /app/manage.py /app/

ENV OPWEN_SESSION_KEY=changeme
ENV OPWEN_SETTINGS=/app/docker/client/webapp.env
