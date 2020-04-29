PY_ENV ?= ./venv

.PHONY: tests
default: build

tests:
	LOKOLE_LOG_LEVEL=CRITICAL $(PY_ENV)/bin/coverage run -m nose2 -v && \
  $(PY_ENV)/bin/coverage xml && \
  $(PY_ENV)/bin/coverage report

lint-swagger:
	find opwen_email_server/swagger -type f -name '*.yaml' | while read file; do \
    echo "==================== $$file ===================="; \
    $(PY_ENV)/bin/swagger-flex --source="$$file" \
  || exit 1; done

lint-python:
	$(PY_ENV)/bin/flake8 opwen_email_server opwen_email_client
	$(PY_ENV)/bin/isort --check-only --recursive opwen_email_server opwen_email_client --virtual-env $(PY_ENV)
	$(PY_ENV)/bin/yapf --recursive --parallel --diff opwen_email_server opwen_email_client tests
	$(PY_ENV)/bin/bandit --recursive opwen_email_server opwen_email_client
	$(PY_ENV)/bin/mypy opwen_email_server opwen_email_client

lint-yaml:
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

lint-helm:
	helm lint --strict ./helm/opwen_cloudserver
	helm template ./helm/opwen_cloudserver > helm.yaml && kubeval --ignore-missing-schemas helm.yaml && rm helm.yaml

lint: lint-python lint-shell lint-swagger lint-docker lint-yaml lint-helm

ci: tests lint

integration-tests:
	docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml build integtest && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml run --rm integtest

clean:
	find . -name '__pycache__' -type d -print0 | xargs -0 rm -rf

clean-storage:
	docker-compose exec api sh -c \
    '"$${PY_ENV}/bin/python" -m opwen_email_server.integration.cli delete-containers --suffix "$(SUFFIX)"'
	docker-compose exec api sh -c \
    '"$${PY_ENV}/bin/python" -m opwen_email_server.integration.cli delete-queues --suffix "$(SUFFIX)"'

build:
	BUILD_TARGET=builder docker-compose build api && \
  docker-compose run --no-deps --rm api cat coverage.xml > coverage.xml
	docker-compose \
    -f docker-compose.yml \
    -f docker/docker-compose.dev.yml \
    -f docker/docker-compose.test.yml \
    -f docker/docker-compose.tools.yml \
    build

start:
	if [ "$(CI)" = "true" ]; then \
    docker-compose up -d; \
  else \
    docker-compose -f docker-compose.yml -f docker/docker-compose.dev.yml up -d --remove-orphans; \
  fi

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

release-pypi:
	docker container create --name webapp "$(DOCKER_USERNAME)/opwenwebapp:$(DOCKER_TAG)" && \
  docker cp "webapp:/app/dist" ./dist && \
  (mv ./dist/pkg.tar.gz "./dist/opwen_email_client-$(DOCKER_TAG).tar.gz" || true) && \
  docker container rm webapp

release-docker:
	for tag in "latest" "$(DOCKER_TAG)"; do ( \
    eval "$(shell find docker -type f -name 'Dockerfile' | while read dockerfile; do grep 'ARG ' "$$dockerfile" | sed 's/^ARG /export /g'; done)"; \
    export BUILD_TARGET="runtime"; \
    export BUILD_TAG="$$tag"; \
    export DOCKER_REPO="$(DOCKER_USERNAME)"; \
    docker-compose build; \
  ) done

release-gh-pages:
	docker container create --name statuspage "$(DOCKER_USERNAME)/opwenstatuspage:$(DOCKER_TAG)" && \
  docker cp "statuspage:/app/lokole" ./build && \
  docker container rm statuspage

release: release-docker release-gh-pages release-pypi

kubeconfig:
	if [ -f "$(PWD)/secrets/kube-config" ]; then \
    cp "$(PWD)/secrets/kube-config" "$(PWD)/kube-config"; \
  fi && \
  if [ ! -f "$(PWD)/kube-config" ]; then \
    curl -sSfL "$(KUBECONFIG_URL)" -o "$(PWD)/kube-config"; \
  fi

renew-cert-k8s: kubeconfig
	docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -v "$(PWD)/kube-config:/secrets/kube-config" \
    setup \
    /app/renew-cert.sh && \
  rm -f "$(PWD)/kube-config"

deploy-k8s: kubeconfig
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

renew-cert:
	echo "Skipping: handled by cron on the VM"

deploy-pypi:
	docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -v "$(PWD)/dist:/dist" \
    setup \
    twine upload --skip-existing -u "$(PYPI_USERNAME)" -p "$(PYPI_PASSWORD)" /dist/*

deploy-docker:
	for tag in "latest" "$(DOCKER_TAG)"; do ( \
    export BUILD_TAG="$$tag"; \
    export DOCKER_REPO="$(DOCKER_USERNAME)"; \
    docker-compose push; \
  ) done

deploy: deploy-pypi deploy-docker
	docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -e LOKOLE_VM_PASSWORD="$(LOKOLE_VM_PASSWORD)" \
    -e LOKOLE_DNS_NAME="$(LOKOLE_DNS_NAME)" \
    setup \
    /app/upgrade.sh vm
