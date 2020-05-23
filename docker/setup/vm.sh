#!/usr/bin/env bash

if [[ "$1" != "install" ]]; then
  cd /home/opwen/lokole || exit 99
  git fetch origin --prune || exit 1
  git reset --hard origin/master || exit 1
  cd - || exit 99
  docker-compose -f /home/opwen/lokole/docker/docker-compose.prod.yml pull || exit 2
  docker-compose -f /home/opwen/lokole/docker/docker-compose.prod.yml up -d || exit 3
  docker system prune -a -f
  exit 0
fi

#
# note: the rest of this script is not intended to be run automatically
# the following steps are merely provided for illustrative purposes for
# setting up a virtual machine to run the system: all steps should be
# run interactively and verified thoroughly
#
hostname="mailserver.lokole.ca"
contact_email="ascoderu.opwen@gmail.com"

#
# set up system
#
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y git curl fail2ban
sudo tee /etc/fail2ban/jail.conf <<EOM
[DEFAULT]
ignoreip = 127.0.0.1
bantime = 300
findtime = 60
maxretry = 3
[sshd]
enabled = true
EOM
sudo service fail2ban restart

#
# set up docker
#
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker opwen
sudo curl -fsSL "https://github.com/docker/compose/releases/download/1.25.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

#
# set up letsencrypt
#
sudo add-apt-repository -y ppa:certbot/certbot
sudo apt-get update
sudo apt-get install -y nginx python-certbot-nginx
sudo sed -i "s/server_name _/server_name ${hostname}/" /etc/nginx/sites-available/default
sudo systemctl reload nginx
sudo certbot --nginx -d "${hostname}" --agree-tos -m "${contact_email}"
echo "0 0 1,15 * * certbot renew 2>&1 | /usr/bin/logger -t update_letsencrypt_renewal" | sudo crontab
sudo chmod 0755 /etc/letsencrypt/{live,archive}

#
# set up app
# important: remember to scp the secrets to the vm manually
#
git clone https://github.com/ascoderu/lokole.git
docker-compose -f lokole/docker/docker-compose.prod.yml pull
docker-compose -f lokole/docker/docker-compose.prod.yml up -d

#
# set up nginx
#
cat >lokole/secrets/nginx.env <<EOM
NGINX_WORKERS=auto
HOSTNAME_WEBAPP=localhost:8080
HOSTNAME_EMAIL_RECEIVE=localhost:8888
HOSTNAME_CLIENT_METRICS=localhost:8888
HOSTNAME_CLIENT_WRITE=localhost:8888
HOSTNAME_CLIENT_READ=localhost:8888
HOSTNAME_CLIENT_REGISTER=localhost:8888
PORT=80
STATIC_ROOT=/home/opwen/lokole/docker/nginx
LETSENCRYPT_DOMAIN=${hostname}
EOM
docker pull ascoderu/opwenserver_nginx
docker run --env-file lokole/secrets/nginx.env --rm ascoderu/opwenserver_nginx sh -c 'mo < /app/nginx.conf.template' | sudo tee /etc/nginx/nginx.conf
docker run --env-file lokole/secrets/nginx.env --rm ascoderu/opwenserver_nginx sh -c 'mo < /app/server.conf.template' | sudo tee /etc/nginx/sites-available/default
sudo systemctl reload nginx
