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

ARG HELM_VERSION=2.16.1
RUN wget -q "https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz" \
  && tar xf "helm-v${HELM_VERSION}-linux-amd64.tar.gz" \
  && mv "linux-amd64/helm" /usr/local/bin/helm \
  && chmod +x /usr/local/bin/helm \
  && rm -rf "linux-amd64" "helm-v${HELM_VERSION}-linux-amd64.tar.gz"

ARG KUBEVAL_VERSION=0.14.0 
RUN wget -q https://github.com/instrumenta/kubeval/releases/download/${KUBEVAL_VERSION}/kubeval-linux-amd64.tar.gz \
  && tar xf kubeval-linux-amd64.tar.gz \
  && cp kubeval /usr/local/bin \
  && rm kubeval-linux-amd64.tar.gz \
  && kubeval --version

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

ARG LOKOLE_SENDGRID_KEY=""
ENV PY_ENV=/usr/local
RUN make ci clean

ENV HOT_RELOAD="True"

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

ENV PY_ENV=/usr/local
