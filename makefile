SHELL := bash -o pipefail

default: build

.github.env: .github.env.gpg
	@gpg --decrypt --batch --passphrase "$(GPG_PASSPHRASE)" .github.env.gpg >.github.env

github-env: .github.env
	@echo "::set-env name=SUFFIX::$(shell cat /proc/sys/kernel/random/uuid)"
	@sed 's/=/::/' <.github.env | sed 's/^export /::set-env name=/'

integration-tests:
	docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml build integtest && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml run --rm integtest

test-emails:
	docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml build integtest && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml run --rm integtest \
  ./3-receive-email-for-client.sh bdd640fb-0667-1ad1-1c80-317fa3b1799d

clean-storage:
	docker-compose exec -T api python -m opwen_email_server.integration.cli delete-containers --suffix "$(SUFFIX)"
	docker-compose exec -T api python -m opwen_email_server.integration.cli delete-queues --suffix "$(SUFFIX)"

ci:
	BUILD_TARGET=builder docker-compose build && \
  docker-compose run --rm --no-deps api ./docker/app/run-ci.sh ----coverage-xml---- | tee coverage.xml && \
  sed -i '1,/----coverage-xml----/d' coverage.xml && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.test.yml build ci

build:
	docker-compose build

start:
	docker-compose up -d --remove-orphans

start-devtools:
	docker-compose -f docker-compose.yml -f docker/docker-compose.tools.yml up -d --remove-orphans

status:
	docker-compose ps; \
  docker-compose ps --services | while read service; do \
    echo "==================== $$service ===================="; \
    docker-compose logs "$$service"; \
  done

logs:
	docker-compose logs --follow --tail=100

stop:
	docker-compose \
    -f docker-compose.yml \
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
    export BUILD_TARGET="runtime"; \
    export BUILD_TAG="$$tag"; \
    export DOCKER_REPO="$(DOCKER_USERNAME)"; \
    docker-compose build; \
  ) done

gh-pages-remote:
	@git remote add ghp "https://$(GITHUB_AUTH_TOKEN)@github.com/ascoderu/lokole.git" && \
  git config --local user.name "Deployment Bot (from Github Actions)" && \
  git config --local user.email "deploy@ascoderu.ca"

release-gh-pages: gh-pages-remote
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

deploy-gh-pages:
	@docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -v "$(PWD)/build:/app/build" \
    -v "$(PWD)/.git:/app/.git" \
    setup \
    ghp-import --push --force --remote ghp --branch gh-pages --message "Update" /app/build

deploy-pypi:
	@docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -v "$(PWD)/dist:/dist" \
    setup \
    twine upload --skip-existing -u "$(PYPI_USERNAME)" -p "$(PYPI_PASSWORD)" /dist/*

deploy-docker:
	@echo "$(DOCKER_PASSWORD)" | docker login --username "$(DOCKER_USERNAME)" --password-stdin && \
  for tag in "latest" "$(DOCKER_TAG)"; do ( \
    export BUILD_TAG="$$tag"; \
    export DOCKER_REPO="$(DOCKER_USERNAME)"; \
    docker-compose push; \
  ) done

deploy: deploy-pypi deploy-gh-pages deploy-docker
	@docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml build setup && \
  docker-compose -f docker-compose.yml -f docker/docker-compose.setup.yml run --rm \
    -e LOKOLE_VM_PASSWORD="$(LOKOLE_VM_PASSWORD)" \
    -e LOKOLE_DNS_NAME="$(LOKOLE_DNS_NAME)" \
    setup \
    /app/upgrade.sh vm
