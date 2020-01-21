FROM debian:buster

# hadolint ignore=DL3009
RUN apt-get update \
 && apt-get install --no-install-recommends -y python3=3.7.3-1 python3-pip=18.1-5 wget=1.20.1-1.1 \
 && pip3 install setuptools==45.1.0

WORKDIR /app
ARG LOKOLE_PORT
ARG LOKOLE_CLIENT_VERSION
ARG INSTALLER_VERSION=${LOKOLE_CLIENT_VERSION}
RUN wget -q "https://raw.githubusercontent.com/ascoderu/opwen-webapp/${INSTALLER_VERSION}/install.py" \
 && USER=root python3 install.py web LocalOnly --system_setup=no --reboot=no --wifi=no --admin=no --log_directory=- --app_root=/web \
 && rm -rf /tmp/install.py install.py

WORKDIR /lib
COPY requirements.txt .
RUN /app/lokole/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY opwen_email_server opwen_email_server
COPY docker/client/integration.py .
COPY docker/client/sync-settings-from-env.sh .

WORKDIR /app
ENV PYTHONPATH=/lib
ENV LOKOLE_IOC=integration.AzureIoc
ENV OPWEN_EMAILS_PER_PAGE=5

EXPOSE ${LOKOLE_PORT}
ENTRYPOINT ["/lib/sync-settings-from-env.sh", "/app/lokole/state/settings.env"]
CMD ["/usr/bin/supervisord", "--configuration=/etc/supervisor/supervisord.conf", "--nodaemon"]
