ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION} AS builder

ARG HADOLINT_VERSION=v1.17.1
RUN wget -q -O /usr/bin/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-$(uname -m)" \
  && chmod +x /usr/bin/hadolint \
  && hadolint --version

ARG SHELLCHECK_VERSION=v0.7.0
RUN wget -q -O /tmp/shellcheck.tar.xz "https://storage.googleapis.com/shellcheck/shellcheck-${SHELLCHECK_VERSION}.linux.$(uname -m).tar.xz" \
  && tar -xJf /tmp/shellcheck.tar.xz -C /usr/bin --strip-components=1 "shellcheck-${SHELLCHECK_VERSION}/shellcheck" \
  && rm /tmp/shellcheck.tar.xz \
  && shellcheck --version

RUN wget -q -O get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 \
  && chmod 700 get_helm.sh \
  && ./get_helm.sh \  
  && helm version

RUN wget -q https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz \
  && tar xf kubeval-linux-amd64.tar.gz \
  && cp kubeval /usr/local/bin

WORKDIR /app

COPY requirements*.txt ./
COPY makefile .
RUN make venv
RUN pip wheel -r requirements.txt -w /deps

COPY . .

ARG LOKOLE_SENDGRID_KEY=""
RUN make ci clean

ENV PY_ENV=/app/venv
ENV HOT_RELOAD="True"

FROM python:${PYTHON_VERSION}-slim AS runtime

RUN groupadd -r opwen \
  && useradd -r -s /bin/false -g opwen opwen

COPY --from=builder /deps /deps
# hadolint ignore=DL3013
RUN pip --no-cache-dir -q install /deps/*.whl

USER opwen
WORKDIR /app

COPY --from=builder /app/docker/docker-entrypoint.sh ./docker/docker-entrypoint.sh
COPY --from=builder /app/docker/app/run-celery.sh ./docker/app/run-celery.sh
COPY --from=builder /app/docker/app/run-gunicorn.sh ./docker/app/run-gunicorn.sh
COPY --from=builder /app/opwen_email_server ./opwen_email_server

ENV PY_ENV=/usr/local

ENTRYPOINT ["/app/docker/docker-entrypoint.sh"]
