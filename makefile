#
# System configuration
#
PYTHON=/usr/bin/python3
VIRTUALENV=/usr/local/bin/virtualenv

#
# Server configuration
#
api_port=8080
api_server=tornado
api_specs=swagger/email-api.yaml
api_runner=./runserver --port=$(api_port) --server=$(api_server) $(api_specs)

#
# You shouldn't need to touch anything below this line.
#
py_env=venv
py_packages=opwen_email_server

.PHONY: default
default: server

$(py_env)/bin/activate: requirements.txt
	test -d $(py_env) || $(VIRTUALENV) --python=$(PYTHON) --no-site-packages $(py_env)
	$(py_env)/bin/pip install -r requirements.txt
	test -f requirements-dev.txt && $(py_env)/bin/pip install -r requirements-dev.txt

venv: $(py_env)/bin/activate

unit-tests: venv
	$(py_env)/bin/nosetests

lint: venv
	$(py_env)/bin/flake8 $(py_packages)

typecheck: venv
	$(py_env)/bin/mypy --silent-imports $(py_packages)

ci: unit-tests lint typecheck

server: venv
	$(api_runner)
