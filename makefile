PY_ENV ?= ./venv

.PHONY: venv tests
default: ci

$(PY_ENV)/requirements.txt.out: requirements.txt requirements-dev.txt requirements-prod.txt
	if [ ! -d $(PY_ENV) ]; then python3 -m venv $(PY_ENV) && $(PY_ENV)/bin/pip install -U pip wheel | tee $(PY_ENV)/requirements.txt.out; fi
	$(PY_ENV)/bin/pip install -r requirements.txt | tee $(PY_ENV)/requirements.txt.out
	$(PY_ENV)/bin/pip install -r requirements-dev.txt | tee $(PY_ENV)/requirements.txt.out
	$(PY_ENV)/bin/pip install -r requirements-prod.txt | tee $(PY_ENV)/requirements.txt.out

venv: $(PY_ENV)/requirements.txt.out

tests: venv
	$(PY_ENV)/bin/coverage run -m nose2 && $(PY_ENV)/bin/coverage report

lint-swagger: venv
	find opwen_email_server/swagger -type f -name '*.yaml' \
    | while read swagger; do $(PY_ENV)/bin/swagger-flex --source="$$swagger" || exit 1; done

lint-python: venv
	$(PY_ENV)/bin/flake8 opwen_email_server
	$(PY_ENV)/bin/isort --check-only --recursive opwen_email_server --virtual-env $(PY_ENV)
	$(PY_ENV)/bin/bandit --recursive opwen_email_server
	$(PY_ENV)/bin/mypy opwen_email_server

lint-docker:
	if command -v hadolint >/dev/null; then \
    find . -type f -name Dockerfile -not -path '$(PY_ENV)/*' | while read file; do \
      hadolint "$$file" \
    || exit 1; done \
  fi

lint-shell:
	if command -v shellcheck >/dev/null; then \
    find . -type f -name '*.sh' -not -path '$(PY_ENV)/*' | while read file; do \
      shellcheck --exclude=SC2181,SC1090,SC1091,SC2103,SC2154 "$$file" \
    || exit 1; done \
  fi

lint: lint-python lint-shell lint-swagger lint-docker

ci: tests lint

integration-tests:
	./tests/integration/wait.sh && \
  ./tests/integration/0-register-client.sh && \
  ./tests/integration/1-client-uploads-emails.sh && sleep 10s && \
  ./tests/integration/2-receive-email-for-client.sh && sleep 10s && \
  ./tests/integration/3-client-downloads-emails.sh && \
  ./tests/integration/assert.sh && \
  rm -rf tests/files/end_to_end/test.out

build:
	docker-compose pull --ignore-pull-failures
	docker-compose build
