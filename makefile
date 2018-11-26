#
# System configuration
#
PYTHON=/usr/bin/python3
SHELLCHECK=/usr/bin/shellcheck

#
# You shouldn't need to touch anything below this line.
#
pwd=$(shell pwd)
py_env=venv
py_packages=opwen_email_server

.PHONY: default
default: server

$(py_env)/bin/activate: requirements.txt
	test -d $(py_env) || $(PYTHON) -m venv $(py_env)
	$(py_env)/bin/pip install -U pip wheel
	$(py_env)/bin/pip install -r requirements.txt
	$(py_env)/bin/pip install -r requirements-dev.txt
	$(py_env)/bin/pip install -r requirements-prod.txt

venv: $(py_env)/bin/activate

unit-tests: venv
	$(py_env)/bin/nosetests --exe --with-coverage --cover-package=$(py_packages) --cover-html

tests: unit-tests

lint-python: venv
	$(py_env)/bin/flake8 $(py_packages)

lint-shell: $(SHELLCHECK)
	$(SHELLCHECK) --exclude=SC2181,SC1090,SC1091,SC2103,SC2154 $$(find . -name '*.sh' -not -path './venv*/*')

lint: lint-python lint-shell

typecheck: venv
	$(py_env)/bin/mypy --ignore-missing-imports $(py_packages)

bandit: venv
	$(py_env)/bin/bandit -r . -x $(py_env)

ci: tests lint typecheck bandit

clean:
	find opwen_email_server -name '__pycache__' -type d -print0 | xargs -0 rm -rf
	find tests -name '__pycache__' -type d -print0 | xargs -0 rm -rf

server: venv
	PY_ENV="$(py_env)" \
    SERVER_WORKERS=1 \
    LOKOLE_LOG_LEVEL=DEBUG \
    TESTING_UI="True" \
    PORT="8080" \
    CONNEXION_SERVER="flask" \
    CONNEXION_SPEC="$(pwd)/opwen_email_server/swagger/email-receive.yaml,$(pwd)/opwen_email_server/swagger/client-write.yaml,$(pwd)/opwen_email_server/swagger/client-read.yaml,$(pwd)/opwen_email_server/swagger/client-register.yaml,$(pwd)/opwen_email_server/swagger/healthcheck.yaml" \
    $(pwd)/docker/app/run-gunicorn.sh

worker: venv
	PY_ENV="$(py_env)" \
    QUEUE_WORKERS=1 \
    LOKOLE_LOG_LEVEL=DEBUG \
    $(pwd)/docker/app/run-celery.sh
