PY_ENV ?= ./venv

.PHONY: venv tests
default: ci

venv: requirements.txt requirements-dev.txt
	if [ ! -d $(PY_ENV) ]; then python3 -m venv $(PY_ENV) && $(PY_ENV)/bin/pip install -U pip wheel; fi
	$(PY_ENV)/bin/pip install -r requirements.txt -r requirements-dev.txt

tests: venv
	LOKOLE_LOG_LEVEL=CRITICAL $(PY_ENV)/bin/coverage run -m nose2 -v && \
  $(PY_ENV)/bin/coverage xml && \
  $(PY_ENV)/bin/coverage report

lint-swagger: venv
	find opwen_email_server/swagger -type f -name '*.yaml' | while read file; do \
    echo "==================== $$file ===================="; \
    $(PY_ENV)/bin/swagger-flex --source="$$file" \
  || exit 1; done

lint-python: venv
	$(PY_ENV)/bin/flake8 opwen_email_server
	$(PY_ENV)/bin/isort --check-only --recursive opwen_email_server --virtual-env $(PY_ENV)
	$(PY_ENV)/bin/yapf --recursive --parallel --diff opwen_email_server tests
	$(PY_ENV)/bin/bandit --recursive opwen_email_server
	$(PY_ENV)/bin/mypy opwen_email_server

lint-yaml: venv
	find . -type f -regex '.*\.ya?ml' -not -path '$(PY_ENV)/*' | grep -v '^./helm/' | while read file; do \
    echo "==================== $$file ===================="; \
    $(PY_ENV)/bin/yamllint "$$file" \
  || exit 1; done

lint-docker:
	if command -v hadolint >/dev/null; then \
    find . -type f -name Dockerfile -not -path '$(PY_ENV)/*' | while read file; do \
      echo "==================== $$file ===================="; \
      hadolint "$$file" \
    || exit 1; done \
  fi

lint-shell:
	if command -v shellcheck >/dev/null; then \
    find . -type f -name '*.sh' -not -path '$(PY_ENV)/*' | while read file; do \
      echo "==================== $$file ===================="; \
      shellcheck "$$file" \
    || exit 1; done \
  fi

lint: lint-python lint-shell lint-swagger lint-docker lint-yaml

ci: tests lint

integration-tests:
	docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml build integtest && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml run --rm integtest

clean:
	find . -name '__pycache__' -type d -print0 | xargs -0 rm -rf

clean-storage:
	docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml build integtest && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml run --rm integtest ./clean.sh "$(SUFFIX)"

build:
	BUILD_TARGET=builder docker-compose build api && \
  docker-compose run --no-deps --rm api cat coverage.xml > coverage.xml
	docker-compose \
    -f docker-compose.yml \
    -f docker/docker-compose.dev.yml \
    -f docker/docker-compose.secrets.yml \
    -f docker/docker-compose.test.yml \
    -f docker/docker-compose.tools.yml \
    build

start:
	if [ "$(CI)" = "true" ]; then \
    docker-compose up -d; \
  else \
    docker-compose -f docker-compose.yml -f docker/docker-compose.dev.yml up -d --remove-orphans; \
  fi

start-azure:
	docker-compose -f docker-compose.yml -f docker/docker-compose.secrets.yml up -d --remove-orphans

start-devtools:
	docker-compose -f docker-compose.yml -f docker/docker-compose.tools.yml up -d --remove-orphans

logs:
	if [ "$(CI)" = "true" ]; then \
    docker-compose ps; \
    docker-compose ps --services | while read service; do \
      echo "==================== $$service ===================="; \
      docker-compose logs "$$service"; \
    done \
  else \
    docker-compose logs --follow --tail=100; \
  fi

stop:
	docker-compose \
    -f docker-compose.yml \
    -f docker/docker-compose.dev.yml \
    -f docker/docker-compose.secrets.yml \
    -f docker/docker-compose.test.yml \
    -f docker/docker-compose.tools.yml \
    down --volumes --timeout=5

verify-build:
	docker pull wagoodman/dive
	docker-compose config | grep -o "image: ascoderu/.*" | sed 's/^image: //' | sort -u | while read image; do \
    echo "==================== $$image ===================="; \
    docker run --rm \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v $(PWD)/.dive-ci:/.dive-ci \
      -e DOCKER_API_VERSION="$(shell docker version -f '{{.Client.APIVersion}}')" \
      -e CI="true" \
      wagoodman/dive "$$image" \
    || exit 1; done

release:
	for tag in "latest" "$(DOCKER_TAG)"; do ( \
    eval "$(shell find docker -type f -name 'Dockerfile' | while read dockerfile; do grep 'ARG ' "$$dockerfile" | sed 's/^ARG /export /g'; done)"; \
    export BUILD_TARGET="runtime"; \
    export BUILD_TAG="$$tag"; \
    export DOCKER_REPO="$(DOCKER_USERNAME)"; \
    docker-compose build && \
    docker-compose push; \
  ) done

kubeconfig:
	if [ -f "$(PWD)/secrets/kube-config" ]; then \
    cp "$(PWD)/secrets/kube-config" "$(PWD)/kube-config"; \
  fi && \
  if [ ! -f "$(PWD)/kube-config" ]; then \
    curl -sSfL "$(KUBECONFIG_URL)" -o "$(PWD)/kube-config"; \
  fi

renew-cert: kubeconfig
	docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -v "$(PWD)/kube-config:/secrets/kube-config" \
    setup \
    /app/renew-cert.sh && \
  rm -f "$(PWD)/kube-config"

deploy: kubeconfig
	docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -e IMAGE_REGISTRY="$(DOCKER_USERNAME)" \
    -e DOCKER_TAG="$(DOCKER_TAG)" \
    -e HELM_NAME="$(HELM_NAME)" \
    -e LOKOLE_DNS_NAME="$(LOKOLE_DNS_NAME)" \
    -v "$(PWD)/kube-config:/secrets/kube-config" \
    setup \
    /app/upgrade.sh && \
  rm -f "$(PWD)/kube-config"
