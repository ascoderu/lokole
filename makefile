#
# System configuration
#
PYTHON=/usr/bin/python3
SHELLCHECK=/usr/bin/shellcheck

#
# Server configuration
#
app_port=8080
api_specs=opwen_email_server/static/email-receive-spec.yaml opwen_email_server/static/client-write-spec.yaml opwen_email_server/static/client-read-spec.yaml opwen_email_server/static/healthcheck-spec.yaml

#
# You shouldn't need to touch anything below this line.
#
py_env=venv
py_packages=opwen_email_server
api_runner=$(py_env)/bin/python runserver.py --port=$(app_port) --ui $(api_specs)

.PHONY: default
default: server

$(py_env)/bin/activate: requirements.txt
	if [ ! -d $(py_env) ]; then \
      $(PYTHON) -m venv $(py_env); \
      $(py_env)/bin/pip install -U pip wheel; \
      $(py_env)/bin/pip install -r requirements.txt; \
      if [ -f requirements-dev.txt ]; then \
        $(py_env)/bin/pip install -r requirements-dev.txt; \
      fi \
    fi

venv: $(py_env)/bin/activate

unit-tests: venv
	$(py_env)/bin/nosetests --exe --with-coverage --cover-package=$(py_packages)

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
	$(api_runner)

inbound-store-worker: venv
	$(py_env)/bin/python opwen_email_server/jobs/store_inbound_emails.py

outbound-send-worker: venv
	$(py_env)/bin/python opwen_email_server/jobs/send_outbound_emails.py

outbound-store-worker: venv
	$(py_env)/bin/python opwen_email_server/jobs/store_outbound_emails.py
