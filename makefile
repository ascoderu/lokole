#
# System configuration
#
PYTHON=/usr/bin/python3

#
# Server configuration
#
api_port=8080
api_server=tornado
api_specs=opwen_email_server/static/email-api-spec.yaml opwen_email_server/static/healthcheck-spec.yaml

#
# You shouldn't need to touch anything below this line.
#
py_env=venv
py_packages=opwen_email_server
api_runner=$(py_env)/bin/python runserver --port=$(api_port) --server=$(api_server) $(api_specs)

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

ci: tests lint typecheck

server: venv
	$(api_runner)

inbound-store-worker: venv
	$(py_env)/bin/python -m opwen_email_server.jobs.store_inbound_emails

outbound-send-worker: venv
	$(py_env)/bin/python -m opwen_email_server.jobs.send_outbound_emails

outbound-store-worker: venv
	$(py_env)/bin/python -m opwen_email_server.jobs.store_written_client_emails

workers: inbound-store-worker outbound-store-worker outbound-send-worker
