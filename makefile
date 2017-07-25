#
# System configuration
#
PYTHON=/usr/bin/python3
NPM=/usr/bin/npm

#
# You shouldn't need to touch anything below this line.
#
py_env=venv
py_packages=opwen_email_client
grunt=./node_modules/grunt/bin/grunt
env=./.env
app_runner=$(py_env)/bin/python ./manage.py devserver

.PHONY: default
default: server

$(py_env)/bin/activate: requirements.txt
	test -d $(py_env) || $(PYTHON) -m venv $(py_env)
	$(py_env)/bin/pip install -U pip wheel
	$(py_env)/bin/pip install -r requirements.txt
	test -f requirements-dev.txt && $(py_env)/bin/pip install -r requirements-dev.txt

venv: $(py_env)/bin/activate

unit-tests: venv
	$(py_env)/bin/nosetests

tests: unit-tests

lint: venv
	$(py_env)/bin/flake8 $(py_packages)

typecheck: venv
	$(py_env)/bin/mypy --silent-imports $(py_packages)

ci: tests lint

$(grunt): package.json bower.json
	$(NPM) install

build-js: $(grunt) Gruntfile.js
	$(grunt)

babel.pot: babel.cfg venv
	$(py_env)/bin/pybabel extract -F babel.cfg -k lazy_gettext -o babel.pot opwen_email_client/webapp

prepare-translations: babel.pot venv
	$(py_env)/bin/pybabel init -i babel.pot -d opwen_email_client/webapp/translations -l $(LANG)

compile-translations: venv
	$(py_env)/bin/pybabel compile -d opwen_email_client/webapp/translations

server: venv compile-translations build-js
	$(app_runner)
