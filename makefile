pwd=$(shell pwd)
py_env=venv

.PHONY: venv tests
default: ci

requirements.txt.out: requirements.txt requirements-dev.txt requirements-prod.txt
	if [ ! -d $(py_env) ]; then python3 -m venv $(py_env) && $(py_env)/bin/pip install -U pip wheel | tee requirements.txt.out; fi
	$(py_env)/bin/pip install -r requirements.txt | tee requirements.txt.out
	$(py_env)/bin/pip install -r requirements-dev.txt | tee requirements.txt.out
	$(py_env)/bin/pip install -r requirements-prod.txt | tee requirements.txt.out

venv: requirements.txt.out

tests: venv
	$(py_env)/bin/coverage run -m nose2 && $(py_env)/bin/coverage report

lint-swagger: venv
	find opwen_email_server/swagger -type f -name '*.yaml' \
    | while read swagger; do $(py_env)/bin/swagger-flex --source="$$swagger" || exit 1; done

lint-python: venv
	$(py_env)/bin/flake8 opwen_email_server
	$(py_env)/bin/isort --check-only --recursive opwen_email_server/**/*.py
	$(py_env)/bin/bandit -r . -x $(py_env)
	$(py_env)/bin/mypy --ignore-missing-imports opwen_email_server

lint-shell:
	shellcheck --exclude=SC2181,SC1090,SC1091,SC2103,SC2154 $$(find . -name '*.sh' -not -path './venv*/*')

lint: lint-python lint-shell lint-swagger

ci: tests lint

integration-tests:
	./tests/integration/0-register-client.sh && \
  ./tests/integration/1-client-uploads-emails.sh && sleep 10s && \
  ./tests/integration/2-receive-email-for-client.sh && sleep 10s && \
  ./tests/integration/3-client-downloads-emails.sh && \
  ./tests/integration/assert.sh && \
  rm -rf tests/files/end_to_end/test.out

stop:
	docker-compose down --volumes

start:
	docker-compose build
	docker-compose pull --ignore-pull-failures
	docker-compose up -d

server: venv
	PY_ENV="$(py_env)" \
    SERVER_WORKERS=1 \
    LOKOLE_LOG_LEVEL=DEBUG \
    TESTING_UI="True" \
    PORT="8080" \
    CONNEXION_SERVER="flask" \
    CONNEXION_SPEC="dir:$(pwd)/opwen_email_server/swagger" \
    $(pwd)/docker/app/run-gunicorn.sh

worker: venv
	PY_ENV="$(py_env)" \
    QUEUE_WORKERS=1 \
    LOKOLE_LOG_LEVEL=DEBUG \
    CELERY_QUEUE_NAMES="all" \
    $(pwd)/docker/app/run-celery.sh
