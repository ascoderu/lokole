#
# You shouldn't need to touch anything below this line.
#
py_env=venv
py_packages=opwen_email_client
grunt=./node_modules/.bin/grunt
env=./.env
app_runner=$(py_env)/bin/python ./manage.py devserver

.PHONY: default
default: server

venv: requirements.txt requirements-dev.txt
	if [ ! -d $(py_env) ]; then python3 -m venv $(py_env) && $(py_env)/bin/pip install -U pip wheel; fi
	$(py_env)/bin/pip install -r requirements.txt
	$(py_env)/bin/pip install -r requirements-dev.txt

unit-tests: venv
	$(py_env)/bin/nosetests --exe --with-coverage --cover-package=$(py_packages)

tests: unit-tests

lint-python: venv
	$(py_env)/bin/flake8 $(py_packages)

lint-shell:
	shellcheck --exclude=SC1090,SC1091,SC2103 $$(find . -name '*.sh' | grep -v 'node_modules/')

lint: lint-python lint-shell

typecheck: venv
	$(py_env)/bin/mypy --ignore-missing-imports $(py_packages)

bandit: venv
	$(py_env)/bin/bandit -r . -x $(py_env)

ci: lint bandit tests

$(grunt): package.json
	yarn install

build-frontend: $(grunt) Gruntfile.js
	$(grunt)

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

server: prepare-server
	$(app_runner)
