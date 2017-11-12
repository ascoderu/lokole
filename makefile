#
# System configuration
#
PYTHON=/usr/bin/python3

#
# Server configuration
#
app_port=8080
api_specs=opwen_email_server/static/email-receive-spec.yaml opwen_email_server/static/client-write-spec.yaml opwen_email_server/static/client-read-spec.yaml opwen_email_server/static/healthcheck-spec.yaml

#
# You shouldn't need to touch anything below this line.
#
compose_file=docker-compose.yml
build_tag=latest
env_file=.env
py_env=venv
py_packages=opwen_email_server
api_runner=$(py_env)/bin/python runserver.py --port=$(app_port) --ui $(api_specs)

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
	$(py_env)/bin/python opwen_email_server/jobs/store_inbound_emails.py

outbound-send-worker: venv
	$(py_env)/bin/python opwen_email_server/jobs/send_outbound_emails.py

outbound-store-worker: venv
	$(py_env)/bin/python opwen_email_server/jobs/store_outbound_emails.py

docker-build-base:
	docker build -f docker/api_base/Dockerfile -t cwolff/opwenserver_api_base:$(build_tag) .
	docker build -f docker/job_base/Dockerfile -t cwolff/opwenserver_job_base:$(build_tag) .

docker-build: docker-build-base
	BUILD_TAG=$(build_tag) APP_PORT=$(app_port) ENV_FILE=$(env_file) docker-compose -f $(compose_file) build

docker-run: $(env_file)
	BUILD_TAG=$(build_tag) APP_PORT=$(app_port) ENV_FILE=$(env_file) docker-compose -f $(compose_file) up

docker-push-base:
	docker push cwolff/opwenserver_api_base:$(build_tag)
	docker push cwolff/opwenserver_job_base:$(build_tag)

docker-push: docker-push-base
	BUILD_TAG=$(build_tag) docker-compose -f $(compose_file) push
