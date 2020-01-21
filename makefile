admin_username=admin3212
admin_password=123456
py_env=venv
log_level=INFO
settings=$(dir $(abspath $(lastword $(MAKEFILE_LIST)))).env

.PHONY: default venv tests
default: server

requirements.txt.out: setup.py requirements.txt requirements-dev.txt
	if [ ! -d $(py_env) ]; then python3 -m venv $(py_env) && $(py_env)/bin/pip install -U pip wheel | tee requirements.txt.out; fi
	$(py_env)/bin/pip install -e . | tee requirements.txt.out
	$(py_env)/bin/pip install -r requirements-dev.txt | tee requirements.txt.out

venv: requirements.txt.out

tests: venv
	$(py_env)/bin/coverage run -m nose2 && $(py_env)/bin/coverage report

lint-python: venv
	$(py_env)/bin/yapf --recursive --parallel --diff opwen_email_client tests
	$(py_env)/bin/flake8 opwen_email_client
	$(py_env)/bin/flake8 *.py
	$(py_env)/bin/isort --check-only --recursive opwen_email_client
	$(py_env)/bin/isort --check-only *.py
	$(py_env)/bin/bandit -x $(py_env) -r opwen_email_client
	$(py_env)/bin/bandit -x $(py_env) *.py

lint-js: node_modules
	yarn run standard opwen_email_client/webapp/static/js/**/*.js

lint: lint-python lint-js

typecheck: venv
	$(py_env)/bin/mypy --ignore-missing-imports opwen_email_client

ci: lint tests

node_modules: package.json
	yarn install

build-frontend: node_modules Gruntfile.js
	yarn run grunt

babel.pot: babel.cfg venv
	$(py_env)/bin/pybabel extract -F babel.cfg -k lazy_gettext -o babel.pot opwen_email_client/webapp

prepare-translations: babel.pot venv
	$(py_env)/bin/pybabel init -i babel.pot -d opwen_email_client/webapp/translations -l $(LANG)

compile-translations: venv
	$(py_env)/bin/pybabel compile -d opwen_email_client/webapp/translations

prepare-server: venv compile-translations build-frontend

clean:
	find opwen_email_client -name '__pycache__' -type d -print0 | xargs -0 rm -rf
	find tests -name '__pycache__' -type d -print0 | xargs -0 rm -rf
	rm -rf dist/ opwen_email_client.egg-info/

bump-version:
	sed -i "s|^__version__ = '[^']*'|__version__ = '$(VERSION)'|g" opwen_email_client/__init__.py

prepare-release: prepare-server bump-version
	$(py_env)/bin/python setup.py sdist

release-pypi: prepare-release
	$(py_env)/bin/pip install twine
	$(py_env)/bin/twine upload -u "$(PYPI_USERNAME)" -p "$(PYPI_PASSWORD)" dist/*

release: release-pypi

admin-user: prepare-server
	OPWEN_SETTINGS=$(settings) \
    $(py_env)/bin/manage.py createadmin \
    --name=$(admin_username) \
    --password=$(admin_password)

server: prepare-server
	OPWEN_SETTINGS=$(settings) \
    $(py_env)/bin/manage.py devserver

worker: prepare-server
	OPWEN_SETTINGS=$(settings) \
    $(py_env)/bin/celery \
    --app=opwen_email_client.webapp.tasks \
    worker \
    --concurrency=2 \
    --loglevel=$(log_level)

cron: prepare-server
	OPWEN_SETTINGS=$(settings) \
    $(py_env)/bin/celery \
    --app=opwen_email_client.webapp.tasks \
    beat \
    --loglevel=$(log_level)

gunicorn: prepare-server
	$(py_env)/bin/gunicorn \
    --workers=2 \
    --bind=127.0.0.1:5000 \
    --env OPWEN_SETTINGS=$(settings) \
    --log-level=$(log_level) \
    opwen_email_client.webapp:app
