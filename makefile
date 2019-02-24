py_env=venv
settings=$(dir $(abspath $(lastword $(MAKEFILE_LIST)))).env

.PHONY: default venv tests
default: server

requirements.txt.out: requirements.txt requirements-dev.txt
	if [ ! -d $(py_env) ]; then python3 -m venv $(py_env) && $(py_env)/bin/pip install -U pip wheel | tee requirements.txt.out; fi
	$(py_env)/bin/pip install -r requirements.txt | tee requirements.txt.out
	$(py_env)/bin/pip install -r requirements-dev.txt | tee requirements.txt.out

venv: requirements.txt.out

tests: venv
	$(py_env)/bin/coverage run -m nose2 && $(py_env)/bin/coverage report

lint-python: venv
	$(py_env)/bin/flake8 opwen_email_client
	$(py_env)/bin/isort --check-only --recursive opwen_email_client/**/*.py

lint-shell:
	shellcheck --exclude=SC1090,SC1091,SC2103 $$(find . -name '*.sh' | grep -v 'node_modules/')

lint-js: node_modules
	yarn run eslint opwen_email_client/webapp/static/js/**/*.js

lint: lint-python lint-shell lint-js

typecheck: venv
	$(py_env)/bin/mypy --ignore-missing-imports opwen_email_client

bandit: venv
	$(py_env)/bin/bandit -r . -x $(py_env)

ci: lint bandit tests

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

release: prepare-server
	echo "$(VERSION)" > version.txt
	$(py_env)/bin/pip install twine
	$(py_env)/bin/python setup.py sdist
	$(py_env)/bin/twine upload -u "$(PYPI_USERNAME)" -p "$(PYPI_PASSWORD)" dist/*

server: prepare-server
	OPWEN_SETTINGS=$(settings) \
    $(py_env)/bin/python ./manage.py devserver

gunicorn: prepare-server
	$(py_env)/bin/gunicorn \
    --workers=2 \
    --bind=127.0.0.1:5000 \
    --env OPWEN_SETTINGS=$(settings) \
    opwen_email_client.webapp:app
