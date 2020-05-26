ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION} AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends mobile-broadband-provider-info=20170903-1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt \
 && rm -rf /tmp/pip-ephem-wheel-cache*

COPY requirements-webapp.txt ./
RUN pip install --no-cache-dir -r requirements-webapp.txt \
 && rm -rf /tmp/pip-ephem-wheel-cache*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && pip wheel --no-cache-dir -r requirements.txt -w /deps \
 && rm -rf /tmp/pip-ephem-wheel-cache*

COPY . .

FROM python:${PYTHON_VERSION}-slim AS runtime

RUN groupadd -r opwen \
  && useradd -r -s /bin/false -g opwen opwen

COPY --from=builder /deps /deps
# hadolint ignore=DL3013
RUN pip --no-cache-dir -q install /deps/*.whl

USER opwen
WORKDIR /app

COPY --from=builder /app/docker/app/run-celery.sh ./docker/app/run-celery.sh
COPY --from=builder /app/docker/app/run-gunicorn.sh ./docker/app/run-gunicorn.sh
COPY --from=builder /app/opwen_email_server ./opwen_email_server
