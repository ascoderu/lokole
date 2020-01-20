FROM debian:buster

RUN apt-get update \
  && apt-get install --no-install-recommends -y python3=3.7.3-1 python3-pip=18.1-5 wget=1.20.1-1.1 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && pip3 install setuptools==45.1.0

WORKDIR /build
ARG CLIENT_VERSION=e12b050
RUN wget -q -O client.tar.gz "https://github.com/ascoderu/opwen-webapp/archive/${CLIENT_VERSION}.tar.gz" \
 && tar --strip-components=1 -x -f client.tar.gz \
 && rm client.tar.gz \
 && python3 setup.py sdist \
 && mkdir /app \
 && mv dist/opwen_email_client-0.0.0.tar.gz /app \
 && mv install.py /app \
 && rm -rf /build

WORKDIR /app

ENV USER=root
RUN python3 install.py web LocalOnly --wifi=no --reboot=no --system_setup=no --client_dist=opwen_email_client-0.0.0.tar.gz

COPY requirements.txt .
RUN lokole/venv/bin/pip install -r requirements.txt

COPY opwen_email_server opwen_email_server
COPY docker/client/integration.py .

# TODO: find a way to inject configuration at runtime
RUN printf '\nLOKOLE_IOC=integration.AzureIoc' >> lokole/state/settings.env

EXPOSE 80
CMD ["/usr/bin/supervisord", "--configuration=/etc/supervisor/supervisord.conf", "--nodaemon"]
