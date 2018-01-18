#!/usr/bin/env bash

readonly usage="Usage: $0 <client-name> <storage-account-name> <storage-account-key> <sim-type> <email-key> <server-tables-name> <server-tables-key>

client-name:              The name that should be assigned to the Opwen device
                          that is being configured by this script. Usually this
                          will be a name that is descriptive for the location
                          where the device will be deployed. The client-name
                          should be globally unique as it is used as the key for
                          a bunch of things.

storage-account-name:     The name of the account on the external storage
                          service (e.g. Azure Blob Storage, Amazon S3, etc.)
                          that the Opwen will use as its target data store.

storage-account-key:      The security key to access the account specified via
                          the <storage-account-name> parameter above.

sim-type:                 The mobile network to which to connect to upload data
                          to the cloud, e.g. Hologram_World or Vodacom_DRC.

email-key:                The security key to access the email sending service
                          (e.g. Sendgrid, Mailgun, etc.)

server-tables-name:       The name of the account on the external storage
                          service (e.g. Azure Blob Storage, Amazon S3, etc.)
                          that the Lokole server uses for tables.

server-tables-key:        The security key to access the account specified via
                          the <server-tables-name> parameter above.
"

################################################################################
# helper methods
################################################################################

info() { echo "$@"; }
error() { echo "$@"; exit 1; }
python_version() { python3 --version 2>&1 | cut -d' ' -f2- | cut -d'.' -f1,2; }
set_timezone() { sudo timedatectl set-timezone "$1"; }
update_system_packages() { sudo apt-get update; sudo apt-get upgrade -y; }
install_system_package() { sudo apt-get install -y "$@"; }
remove_system_package() { sudo apt-get remove -y "$@"; }
install_python_package() { pip install "$1"; }
update_python_package() { pip install --upgrade "$1"; }
write_file() { mkdir -p "$(dirname "$1")"; sudo tee "$1" > /dev/null; }
replace_file() { sudo sed -i "$1" "$2"; }
create_directory() { mkdir -p "$1"; }
create_root_directory() { sudo mkdir -p "$1"; }
create_link() { sudo ln -s "$1" "$2" || true; }
delete() { if [ ! -L "$1" ]; then sudo rm -rf "$1"; else sudo unlink "$1"; fi }
make_executable() { sudo chmod a+x "$1"; }
enter_virtualenv() { if [ ! -d "$1/bin" ]; then python3 -m venv "$1"; fi; . "$1/bin/activate"; }
exit_virtualenv() { deactivate; }
change_password() { echo "$1:$2" | sudo chpasswd; }
required_param() { [ -z "$1" ] && echo "Missing required parameter: $2" && (echo "$3" | head -1) && exit 1; }
random_string() { head /dev/urandom | tr -dc '_A-Z-a-z-0-9' | head -c"${1:-16}"; echo; }
disable_system_power_management() { sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target; }
get_system_ram_kb() { grep 'MemTotal' '/proc/meminfo' | cut -d':' -f2 | sed 's/^ *//g' | cut -d' ' -f1; }
min() { if [ "$1" -lt "$2" ]; then echo "$1"; else echo "$2"; fi; }
create_root_cron() { (sudo crontab -l || true; echo "$1 $2") 2>&1 | grep -v 'no crontab for' | sort -u | sudo crontab -; }
http_delete() { /usr/bin/curl --request 'DELETE' "$@"; }
http_post_json() { /usr/bin/curl --header 'Content-Type: application/json' --request 'POST' "$@"; }
reload_daemons() { sudo service supervisor start; sudo supervisorctl reread; sudo supervisorctl update; }

set_locale() {
local locale="$1"

local locale_script='/etc/profile.d/set-locale.sh'
local locale_command="export LANGUAGE='${locale}'; export LC_ALL='${locale}'; export LANG='${locale}'; export LC_TYPE='${locale}';"

sudo locale-gen "${locale}"
sudo update-locale
eval "${locale_command}"

echo "${locale_command}" | write_file "${locale_script}"
make_executable "${locale_script}"
}

create_daemon() {
local daemon_name="$1"
local script="$2"
local runas="${3:-${USER}}"
local stdlogfile="${4:-/var/log/${daemon_name}.out.log}"
local errlogfile="${5:-/var/log/${daemon_name}.err.log}"

write_file "/etc/supervisor/conf.d/${daemon_name}.conf" << EOF
[program:${daemon_name}]
command=${script}
autostart=true
autorestart=true
startretries=3
stderr_logfile=${errlogfile}
stdout_logfile=${stdlogfile}
user=${runas}
EOF
reload_daemons
}

################################################################################
# command line interface
################################################################################

case $1 in -h|--help) error "${usage}";; esac

readonly opwen_webapp_config_client_name="$1"
readonly opwen_webapp_config_remote_account_name="$2"
readonly opwen_webapp_config_remote_account_key="$3"
readonly sim_type="$4"
readonly email_account_key="$5"
readonly server_tables_account_name="$6"
readonly server_tables_account_key="$7"
readonly opwen_network_name='Lokole'
readonly opwen_network_password='Ascoderu'
readonly opwen_webapp_sync_schedule='34 * * * *'
readonly opwen_server_read_host='api.mailserver.read.lokole.ca'
readonly opwen_server_write_host='api.mailserver.write.lokole.ca'
readonly opwen_server_inbox_host='api.mailserver.inbox.lokole.ca'

required_param "${opwen_webapp_config_client_name}" 'client-name' "${usage}"
required_param "${opwen_webapp_config_remote_account_name}" 'storage-account-name' "${usage}"
required_param "${opwen_webapp_config_remote_account_key}" 'storage-account-key' "${usage}"
required_param "${sim_type}" 'sim-type' "${usage}"
required_param "${email_account_key}" 'email-key' "${usage}"
required_param "${server_tables_account_name}" 'server-tables-name' "${usage}"
required_param "${server_tables_account_key}" 'server-tables-key' "${usage}"

set -o errexit
set -o pipefail


################################################################################
# pre-install setup
################################################################################

opwen_user="${USER}"
opwen_user_password="$(random_string 8)"
info "Password of ${opwen_user} set to ${opwen_user_password}"

set_locale 'en_GB.UTF-8'
set_timezone 'Etc/UTC'
update_system_packages
change_password "${opwen_user}" "${opwen_user_password}"


################################################################################
# install wifi
################################################################################

install_system_package 'hostapd' 'dnsmasq'

opwen_ip_base='10.0.0'
opwen_ip="${opwen_ip_base}.1"

write_file '/etc/hosts' << EOF
::1		localhost ip6-localhost ip6-loopback
ff02::1		ip6-allnodes
ff02::2		ip6-allrouters
127.0.0.1	localhost
127.0.0.1	${HOSTNAME}
127.0.1.1	${HOSTNAME}
${opwen_ip}	www.lokole.com
${opwen_ip}	www.lokole.org
${opwen_ip}	www.lokole.ca
${opwen_ip}	www.lokole.cd
${opwen_ip}	www.lokole
${opwen_ip}	www.opwen.com
${opwen_ip}	www.opwen.org
${opwen_ip}	www.opwen.ca
${opwen_ip}	www.opwen.cd
${opwen_ip}	www.opwen
${opwen_ip}	www.ascoderu.com
${opwen_ip}	www.ascoderu.org
${opwen_ip}	www.ascoderu.ca
${opwen_ip}	www.ascoderu.cd
${opwen_ip}	lokole.com
${opwen_ip}	lokole.org
${opwen_ip}	lokole.ca
${opwen_ip}	lokole.cd
${opwen_ip}	lokole
${opwen_ip}	opwen.com
${opwen_ip}	opwen.org
${opwen_ip}	opwen.ca
${opwen_ip}	opwen.cd
${opwen_ip}	opwen
${opwen_ip}	ascoderu.com
${opwen_ip}	ascoderu.org
${opwen_ip}	ascoderu.ca
${opwen_ip}	ascoderu.cd
EOF

case "${HOSTNAME}" in
  OrangePI|orangepizero) ht_capab='[HT40][DSS_CCK-40]'              ;;
  raspberrypi)           ht_capab='[HT40][SHORT-GI-20][DSS_CCK-40]' ;;
  *)                     error "${HOSTNAME} unsupported"            ;;
esac

write_file '/etc/dnsmasq.conf' << EOF
log-facility=/var/log/dnsmasq.log
dhcp-range=${opwen_ip_base}.10,${opwen_ip_base}.250,12h
interface=wlan0
no-resolv
log-queries
server=8.8.8.8
EOF

write_file '/etc/network/interfaces' << EOF
auto lo
iface lo inet loopback

auto eth0
allow-hotplug eth0
iface eth0 inet dhcp

auto wlan0
allow-hotplug wlan0
iface wlan0 inet static
  post-up service hostapd restart
  post-up service dnsmasq restart
  address ${opwen_ip}
  netmask 255.255.255.0
wireless-power off

auto ppp0
iface ppp0 inet wvdial
EOF

write_file '/etc/hostapd/hostapd.conf' << EOF
interface=wlan0
driver=nl80211
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1
ht_capab=${ht_capab}
macaddr_acl=0
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
ssid=${opwen_network_name}
wpa_passphrase=${opwen_network_password}
EOF

replace_file 's@^DAEMON_CONF=$@DAEMON_CONF=/etc/hostapd/hostapd.conf@' '/etc/init.d/hostapd'
disable_system_power_management


################################################################################
# install webapp
################################################################################

install_system_package 'python3' 'python3-pip' 'python3-venv' 'python3-dev' 'libffi-dev' 'bcrypt'

opwen_webapp_run_directory="/home/${opwen_user}/www/state/opwen-webapp"
opwen_webapp_virtualenv="${opwen_webapp_run_directory}/venv"
opwen_webapp_service='opwen_email_client'
opwen_webapp_directory="${opwen_webapp_virtualenv}/lib/python$(python_version)/site-packages/${opwen_webapp_service}/webapp"

create_directory "${opwen_webapp_run_directory}"
create_directory "${opwen_webapp_virtualenv}"

enter_virtualenv "${opwen_webapp_virtualenv}"
update_python_package 'pip'
update_python_package 'setuptools'
install_python_package 'wheel'

install_python_package "${opwen_webapp_service}"
"${opwen_webapp_virtualenv}/bin/pybabel" compile -d "${opwen_webapp_directory}/translations"

delete "${HOME}/.cache/pip"


################################################################################
# register webapp
################################################################################


install_system_package 'libssl-dev'
registration_virtualenv="$(mktemp -d)"
opwen_webapp_config_client_id="$(random_string 32)"
opwen_webapp_config_client_domain="${opwen_webapp_config_client_name}.lokole.ca"

exit_virtualenv
enter_virtualenv "${registration_virtualenv}"
update_python_package 'pip'
update_python_package 'setuptools'
install_python_package 'wheel'

install_python_package 'opwen_email_server'

"${registration_virtualenv}/bin/registerclient.py" \
    --tables_account="${server_tables_account_name}" \
    --tables_key="${server_tables_account_key}" \
    --client_account="${opwen_webapp_config_remote_account_name}" \
    --client_key="${opwen_webapp_config_remote_account_key}" \
    --client="${opwen_webapp_config_client_id}" \
    --domain="${opwen_webapp_config_client_domain}"

exit_virtualenv
delete "${HOME}/.cache/pip"
delete "${registration_virtualenv}"
remove_system_package 'libssl-dev'
enter_virtualenv "${opwen_webapp_virtualenv}"


################################################################################
# setup webapp environment
################################################################################

opwen_webapp_config_session_key="$(random_string 32)"
opwen_webapp_config_password_salt="$(random_string 16)"
opwen_webapp_admin_secret="$(random_string 32)"
opwen_webapp_envs="${opwen_webapp_run_directory}/env"

write_file "${opwen_webapp_envs}" << EOF
export OPWEN_STATE_DIRECTORY='${opwen_webapp_run_directory}'
export OPWEN_SESSION_KEY='${opwen_webapp_config_session_key}'
export OPWEN_PASSWORD_SALT='${opwen_webapp_config_password_salt}'
export OPWEN_ADMIN_SECRET='${opwen_webapp_admin_secret}'
export OPWEN_REMOTE_ACCOUNT_NAME='${opwen_webapp_config_remote_account_name}'
export OPWEN_REMOTE_ACCOUNT_KEY='${opwen_webapp_config_remote_account_key}'
export OPWEN_CLIENT_ID='${opwen_webapp_config_client_id}'
export OPWEN_CLIENT_NAME='${opwen_webapp_config_client_name}'
export OPWEN_EMAIL_SERVER_READ_API='${opwen_server_read_host}'
export OPWEN_EMAIL_SERVER_WRITE_API='${opwen_server_write_host}'
EOF


################################################################################
# install server
################################################################################

install_system_package 'nginx'
install_system_package 'supervisor'

memory_per_worker_kb=200000
max_workers=4
opwen_webapp_timeout_seconds=300
opwen_webapp_workers=$(min $(($(get_system_ram_kb) / memory_per_worker_kb)) ${max_workers})
opwen_webapp_socket="${opwen_webapp_run_directory}/webapp.sock"

opwen_webapp_script="${opwen_webapp_run_directory}/webapp.sh"
write_file "${opwen_webapp_script}" << EOF
#!/usr/bin/env sh
. '${opwen_webapp_envs}'

'${opwen_webapp_virtualenv}/bin/gunicorn' \
  --timeout='${opwen_webapp_timeout_seconds}' \
  --workers='${opwen_webapp_workers}' \
  --bind='unix:${opwen_webapp_socket}' \
  '${opwen_webapp_service}.webapp:app'
EOF
make_executable "${opwen_webapp_script}"

create_daemon \
  "${opwen_webapp_service}" \
  "${opwen_webapp_script}" \
  "${opwen_user}" \
  "${opwen_webapp_run_directory}/out.log" \
  "${opwen_webapp_run_directory}/err.log"

create_root_directory '/var/log/nginx'
write_file "/etc/nginx/sites-available/${opwen_webapp_service}" << EOF
server {
  listen 80;
  server_name localhost;

  location = /favicon.ico { alias ${opwen_webapp_directory}/static/favicon.ico; }
  location /static/ { root ${opwen_webapp_directory}; }
  location / { include proxy_params; proxy_pass http://unix:${opwen_webapp_socket}; }
}
EOF
create_link "/etc/nginx/sites-available/${opwen_webapp_service}" '/etc/nginx/sites-enabled'
delete '/etc/nginx/sites-available/default'

write_file '/etc/nginx/nginx.conf' << EOF
user www-data;
worker_processes 4;
pid /run/nginx.pid;

events {
  worker_connections 768;
}

http {
  sendfile on;
  tcp_nopush on;
  tcp_nodelay on;
  keepalive_timeout 65;
  types_hash_max_size 2048;
  include /etc/nginx/mime.types;
  default_type application/octet-stream;
  ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
  ssl_prefer_server_ciphers on;
  access_log /var/log/nginx/access.log;
  error_log /var/log/nginx/error.log;
  gzip on;
  gzip_disable "msie6";
  include /etc/nginx/conf.d/*.conf;
  include /etc/nginx/sites-enabled/*;

  fastcgi_connect_timeout ${opwen_webapp_timeout_seconds};
  fastcgi_send_timeout ${opwen_webapp_timeout_seconds};
  fastcgi_read_timeout ${opwen_webapp_timeout_seconds};
}
EOF

################################################################################
# install network stick
################################################################################

install_system_package 'usb-modeswitch' 'usb-modeswitch-data' 'ppp' 'wvdial' 'cron' 'curl'

internet_modem_config_e303='/etc/usb_modeswitch.d/12d1:14fe'
internet_modem_config_e353='/etc/usb_modeswitch.d/12d1:1f01'
internet_modem_config_e3131='/etc/usb_modeswitch.d/12d1:155b'
internet_dialer_config='/etc/wvdial.conf'
opwen_webapp_email_sync_script="${opwen_webapp_run_directory}/email-sync.sh"

if [ "${sim_type}" = 'Hologram_World' ]; then
write_file "${internet_dialer_config}" << EOF
[Dialer Defaults]
Init1 = ATZ
Init2 = ATQ0
Init3 = AT+CGDCONT=1,"IP","apn.konekt.io"
Phone = *99***1#
Stupid Mode = 1
Username = { }
Password = { }
Modem Type = Analog Modem
Modem = /dev/ttyUSB0
IDSN = 0
EOF
else
error "Unrecognized sim-type: ${sim_type}"
fi

write_file "${internet_modem_config_e303}" << EOF
DefaultVendor = 0x12d1
DefaultProduct = 0x14fe
TargetVendor = 0x12d1
TargetProduct = 0x1506
MessageContent = "55534243123456780000000000000011062000000101000100000000000000"
EOF

write_file "${internet_modem_config_e353}" << EOF
DefaultVendor = 0x12d1
DefaultProduct = 0x1f01
TargetVendor = 0x12d1
TargetProduct = 0x1001
MessageContent = "55534243123456780000000000000011060000000000000000000000000000"
EOF

write_file "${internet_modem_config_e3131}" << EOF
DefaultVendor = 0x12d1
DefaultProduct = 0x155b
TargetVendor = 0x12d1
TargetProduct = 0x1506
MessageContent = "55534243123456780000000000000011062000000100000000000000000000"
EOF

write_file '/etc/ppp/peers/wvdial' << EOF
noauth
name wvdial
usepeerdns
defaultroute
replacedefaultroute
EOF

write_file "${opwen_webapp_email_sync_script}" << EOF
#!/usr/bin/env sh

sync_secret='${opwen_webapp_admin_secret}'
dialer_config='${internet_dialer_config}'
dialer_logfile="\$(mktemp dialer.log.XXXXXX)"
dialer_pidfile="\$(mktemp dialer.pid.XXXXXX)"
modem_target_mode='1506'

modem_is_e303() { lsusb | grep 'Huawei' | grep -q '12d1:14fe'; }
modem_is_e353() { lsusb | grep 'Huawei' | grep -q '12d1:1f01'; }
modem_is_e3131() { lsusb | grep 'Huawei' | grep -q '12d1:155b'; }
modem_is_plugged() { lsusb | grep 'Huawei' | grep -q '12d1:'; }
modem_is_setup() { lsusb | grep 'Huawei' | grep -q "12d1:\${modem_target_mode}"; }
dialer_is_running() { test -f "\${dialer_pidfile}" && read pid < "\${dialer_pidfile}" && ps -p "\${pid}" > /dev/null; }
connect_to_internet() { /usr/bin/wvdial --config="\${dialer_config}" 2> "\${dialer_logfile}" & echo \$! > "\${dialer_pidfile}"; }
dialer_is_connected() { test -f "\${dialer_logfile}" && grep -q 'secondary DNS address' "\${dialer_logfile}"; }
kill_dialer() { test -f "\${dialer_pidfile}" && read pid < "\${dialer_pidfile}" && kill "\${pid}" && rm "\${dialer_pidfile}" && rm "\${dialer_logfile}"; }
sync_emails() { /usr/bin/curl "http://localhost/sync?secret=\${sync_secret}"; }

setup_modem() {
  if   modem_is_e353;  then modem_target_mode='1001'; /usr/sbin/usb_modeswitch --config-file '${internet_modem_config_e353}'
  elif modem_is_e303;  then modem_target_mode='1506'; /usr/sbin/usb_modeswitch --config-file '${internet_modem_config_e303}'
  elif modem_is_e3131; then modem_target_mode='1506'; /usr/sbin/usb_modeswitch --config-file '${internet_modem_config_e3131}'
  else exit 1;         fi
}

main() {
  if ! modem_is_plugged; then
    echo 'Modem not plugged in, exitting' >&2
    exit 1
  fi

  if ! modem_is_setup; then
    echo 'Setting up modem...'
    setup_modem
    while ! modem_is_setup; do sleep 1s; done
    echo '...done, modem is now set up'
  fi

  if ! dialer_is_running; then
    echo 'Dialing up...'
    connect_to_internet
    while ! dialer_is_connected; do sleep 1s; done
    echo '...done, connection to internet is established'
  fi

  echo 'Syncing emails...'
  sync_emails
  echo '...done, emails are synced'

  echo 'Killing dialer...'
  kill_dialer
  echo '...done, connection to internet is terminated'
}

main
EOF
make_executable "${opwen_webapp_email_sync_script}"

create_root_cron "${opwen_webapp_sync_schedule}" "${opwen_webapp_email_sync_script}"


################################################################################
# setup email
################################################################################

opwen_cloudserver_endpoint="http://${opwen_server_inbox_host}/api/email/sendgrid/${opwen_webapp_config_client_id}"

http_delete \
     --header "Authorization: Bearer ${email_account_key}" \
     "https://api.sendgrid.com/v3/user/webhooks/parse/settings/${opwen_webapp_config_client_domain}"

http_post_json \
    --header "Authorization: Bearer ${email_account_key}" \
    --data "{\"hostname\":\"${opwen_webapp_config_client_domain}\",\"url\":\"${opwen_cloudserver_endpoint}\",\"spam_check\":true,\"send_raw\":true}" \
    'https://api.sendgrid.com/v3/user/webhooks/parse/settings'

info "
Now complete the email setup for the device.

Login to https://domain-dns.com and:
1.1) Click 'edit zone' on lokole.ca
1.2) Click 'add host'
1.3) Into the 'host' box, write: ${opwen_webapp_config_client_name}
1.4) Into the 'mx1' box, write: mx.sendgrid.net
1.5) Click 'add host'
"


################################################################################
# start running
################################################################################

info "Last step! Restart the machine so that all changes take full effect:
sudo shutdown --reboot now
"
