pwd=$(shell pwd)
py_env=venv

.PHONY: default tests
default: run

venv: requirements.txt requirements-dev.txt requirements-prod.txt
	if [ ! -d $(py_env) ]; then python3 -m venv $(py_env) && $(py_env)/bin/pip install -U pip wheel; fi
	$(py_env)/bin/pip install -r requirements.txt
	$(py_env)/bin/pip install -r requirements-dev.txt
	$(py_env)/bin/pip install -r requirements-prod.txt

tests: venv
	$(py_env)/bin/nosetests --exe --with-coverage --cover-package=opwen_email_server --cover-html

lint-swagger: venv
	find opwen_email_server/swagger -type f -name '*.yaml' \
    | while read swagger; do $(py_env)/bin/swagger-flex --source="$$swagger" || exit 1; done

lint-python: venv
	$(py_env)/bin/flake8 opwen_email_server

lint-shell:
	shellcheck --exclude=SC2181,SC1090,SC1091,SC2103,SC2154 $$(find . -name '*.sh' -not -path './venv*/*')

lint: lint-python lint-shell lint-swagger

typecheck: venv
	$(py_env)/bin/mypy --ignore-missing-imports opwen_email_server

bandit: venv
	$(py_env)/bin/bandit -r . -x $(py_env)

ci: tests lint typecheck bandit

clean:
	rm -rf $$(find opwen_email_server -name '__pycache__' -type d)
	rm -rf $$(find tests -name '__pycache__' -type d)
	rm -rf $(py_env) .mypy_cache cover .coverage
	docker-compose down && rm -rf volumes register.json download.json

run:
	docker-compose up --build

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
