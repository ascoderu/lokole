FROM debian:buster

RUN apt-get update && apt-get install -y python3

WORKDIR /app
COPY install.py .
RUN python3 install.py web LocalOnly --wifi=no --reboot=no --system_setup=no

EXPOSE 80
CMD ["/usr/bin/supervisord", "--configuration=/etc/supervisor/supervisord.conf", "--nodaemon"]
