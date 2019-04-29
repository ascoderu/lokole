ARG PYTHON_VERSION=3.6
FROM python:${PYTHON_VERSION} AS builder

ARG HADOLINT_VERSION=v1.16.0
RUN wget -q -O /usr/bin/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-$(uname -m)" \
  && chmod +x /usr/bin/hadolint \
  && hadolint --version

ARG SHELLCHECK_VERSION=v0.6.0
RUN wget -q -O /tmp/shellcheck.tar.xz "https://storage.googleapis.com/shellcheck/shellcheck-${SHELLCHECK_VERSION}.linux.$(uname -m).tar.xz" \
  && tar -xJf /tmp/shellcheck.tar.xz -C /usr/bin --strip-components=1 "shellcheck-${SHELLCHECK_VERSION}/shellcheck" \
  && rm /tmp/shellcheck.tar.xz \
  && shellcheck --version

WORKDIR /src

COPY requirements*.txt ./
COPY makefile .
RUN make venv
RUN pip wheel -r requirements.txt -w /deps

COPY . .

RUN make ci clean

FROM python:${PYTHON_VERSION}-slim AS runtime

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates=20161130+nmu1+deb9u1 \
  && rm -rf /var/lib/apt/lists/* \
  && groupadd -r opwen \
  && useradd -r -s /bin/false -g opwen opwen

COPY --from=builder /deps /deps
# hadolint ignore=DL3013
RUN pip --no-cache-dir -q install /deps/*.whl

USER opwen
WORKDIR /app

COPY --from=builder /src/docker/docker-entrypoint.sh .
COPY --from=builder /src/docker/app/run-celery.sh .
COPY --from=builder /src/docker/app/run-flower.sh .
COPY --from=builder /src/docker/app/run-gunicorn.sh .
COPY --from=builder /src/opwen_email_server ./opwen_email_server

ENV PY_ENV="/usr/local"
ENV TESTING_UI="False"
ENV CONNEXION_SPEC="SET_ME"
ENV SERVER_WORKERS="1"
ENV QUEUE_WORKERS="1"
ENV LOKOLE_LOG_LEVEL="INFO"
ENV PORT=8080

EXPOSE ${PORT}
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["bash"]
