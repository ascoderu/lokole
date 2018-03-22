#!/usr/bin/env bash

#
# install docker and docker-compose
#
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  sudo apt-get update
  sudo apt-get install -y docker-ce
  sudo usermod -aG docker "${USER}"
  sudo curl -L "https://github.com/docker/compose/releases/download/1.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi

#
# setup systemd
#
app_base="/home/${USER}/opwen_cloudserver"
systemd_unit="${app_base}/opwen_cloudserver.service"
systemd_start="${app_base}/systemd_start.sh"
systemd_stop="${app_base}/systemd_stop.sh"

mkdir -p "${app_base}"

curl -L "https://raw.githubusercontent.com/ascoderu/opwen-cloudserver/master/setup/systemd_start.sh" -o "${systemd_start}"
chmod +x "${systemd_start}"

curl -L "https://raw.githubusercontent.com/ascoderu/opwen-cloudserver/master/setup/systemd_stop.sh" -o "${systemd_stop}"
chmod +x "${systemd_stop}"

cat > "${systemd_unit}" << EOF
[Unit]
Description=Run opwen-cloudserver via docker-compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${app_base}
ExecStart=${systemd_start}
ExecStop=${systemd_stop}
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
sudo mv "${systemd_unit}" /etc/systemd/system
sudo systemctl enable opwen_cloudserver
