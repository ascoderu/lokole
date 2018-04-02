#!/usr/bin/env bash

readonly usage="Usage: $0 <version> <client-name> <storage-account-name> <storage-account-key> <email-key> <server-tables-name> <server-tables-key> <cloudflare-user> <cloudflare-key> <cloudflare-zone> <sync-schedule>

Parameters:
--------------------------

version:                  The version of the email app to install.

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

email-key:                The security key to access the email sending service
                          (e.g. Sendgrid, Mailgun, etc.)

server-tables-name:       The name of the account on the external storage
                          service (e.g. Azure Blob Storage, Amazon S3, etc.)
                          that the Lokole server uses for tables.

server-tables-key:        The security key to access the account specified via
                          the <server-tables-name> parameter above.

cloudflare-user:          The user name for the Cloudflare account associated
                          with the Lokole DNS.

cloudflare-key:           The access key for the Cloudflare account associated
                          with the Lokole DNS.

cloudflare-zone:          The zone for the Cloudflare account associated with
                          the Lokole DNS.

sync-schedule:            How often the Lokole should sync with the server. In
                          cron syntax. Example: '34 * * * *' for once per hour.

Environment variables:
--------------------------

LOKOLE_BASEDIR:           The Lokole configuration files will get installed into
                          this directory. Defaults to ~/opwen_config.

LOKOLE_STATEDIR:          The Lokole state files will get stored in this
                          directory. Defaults to ~/opwen_state.

LOKOLE_PORT:              The Lokole application will run on this port. Defaults
                          to 80.

DOCKER_USERNAME:          The user from which the Lokole docker images will be
                          pulled. Defaults to cwolff.
"

case "$1" in -h|--help) echo "${usage}" && exit 1;; esac

required_param() { [ -z "$1" ] && echo "Missing required parameter: $2" && (echo "$3" | head -1) && exit 1; }
check_dependency() { if ! command -v "$1" >/dev/null; then echo "Missing dependency: $1" && exit 1; fi }
random_string() { head /dev/urandom | tr -dc '_A-Z-a-z-0-9' | head -c"${1:-16}"; echo; }
set_default() { if [ -z "$1" ]; then echo "$2"; else echo "$1"; fi }

readonly version="$1"
readonly opwen_webapp_config_client_name="$2"
readonly opwen_webapp_config_remote_account_name="$3"
readonly opwen_webapp_config_remote_account_key="$4"
readonly email_account_key="$5"
readonly server_tables_account_name="$6"
readonly server_tables_account_key="$7"
readonly cloudflare_user="$8"
readonly cloudflare_key="$9"
readonly cloudflare_zone="${10}"
readonly sync_schedule="${11}"

required_param "${version}" 'version' "${usage}"
required_param "${opwen_webapp_config_client_name}" 'client-name' "${usage}"
required_param "${opwen_webapp_config_remote_account_name}" 'storage-account-name' "${usage}"
required_param "${opwen_webapp_config_remote_account_key}" 'storage-account-key' "${usage}"
required_param "${email_account_key}" 'email-key' "${usage}"
required_param "${server_tables_account_name}" 'server-tables-name' "${usage}"
required_param "${server_tables_account_key}" 'server-tables-key' "${usage}"
required_param "${cloudflare_user}" 'cloudflare-user' "${usage}"
required_param "${cloudflare_key}" 'cloudflare-key' "${usage}"
required_param "${cloudflare_zone}" 'cloudflare-zone' "${usage}"
required_param "${sync_schedule}" 'sync-schedule' "${usage}"

check_dependency "crontab"
check_dependency "curl"
check_dependency "docker"
check_dependency "systemctl"

readonly basedir="$(set_default "${LOKOLE_BASEDIR}" "${HOME}/opwen_config")"
readonly statedir="$(set_default "${LOKOLE_STATEDIR}" "${HOME}/opwen_state")"
readonly port="$(set_default "${LOKOLE_PORT}" "80")"
readonly dockeruser="$(set_default "${DOCKER_USERNAME}" "cwolff")"

mkdir -p "${basedir}" "${statedir}"

#
# set up app
#

cat > "${basedir}/secrets.env" << EOF
OPWEN_ADMIN_SECRET=$(random_string 32)
OPWEN_CLIENT_ID=$(random_string 32)
OPWEN_PASSWORD_SALT=$(random_string 32)
OPWEN_SESSION_KEY=$(random_string 32)
OPWEN_CLIENT_NAME=${opwen_webapp_config_client_name}
OPWEN_CLOUDFLARE_KEY=${cloudflare_key}
OPWEN_CLOUDFLARE_USER=${cloudflare_user}
OPWEN_CLOUDFLARE_ZONE=${cloudflare_zone}
OPWEN_REMOTE_ACCOUNT_KEY=${opwen_webapp_config_remote_account_key}
OPWEN_REMOTE_ACCOUNT_NAME=${opwen_webapp_config_remote_account_name}
OPWEN_SENDGRID_KEY=${email_account_key}
OPWEN_SERVER_TABLES_ACCOUNT_KEY=${server_tables_account_key}
OPWEN_SERVER_TABLES_ACCOUNT_NAME=${server_tables_account_name}
EOF

docker pull "${dockeruser}/opwenclient_nginx:${version}"
docker pull "${dockeruser}/opwenclient_app:${version}"

cat > "${basedir}/docker-start.sh" << EOF
#!/usr/bin/env sh
docker network create opwen_webapp

docker run \\
  --detach \\
  --net "opwen_webapp" \\
  --env-file "${basedir}/secrets.env" \\
  --volume "${statedir}:/state" \\
  --name "opwenclient_app" \\
  "${dockeruser}/opwenclient_app:${version}"

docker run \\
  --detach \\
  --net "opwen_webapp" \\
  --publish "${port}:80" \\
  --name "opwenclient_nginx" \\
  "${dockeruser}/opwenclient_nginx:${version}"
EOF
chmod a+x "${basedir}/docker-start.sh"

cat > "${basedir}/docker-stop.sh" << EOF
docker stop "opwenclient_app" "opwenclient_nginx"
docker rm "opwenclient_app" "opwenclient_nginx"
docker network remove opwen_webapp
EOF
chmod a+x "${basedir}/docker-stop.sh"

#
# set up autostart
#

cat > "${basedir}/opwen_webapp.service" << EOF
[Unit]
Description=Run opwen-webapp via docker
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${basedir}
ExecStart=${basedir}/docker-start.sh
ExecStop=${basedir}/docker-stop.sh
TimeoutStartSec=0
TimeoutStopSec=0

[Install]
WantedBy=multi-user.target
EOF
sudo mv "${basedir}/opwen_webapp.service" /etc/systemd/system
sudo systemctl enable opwen_webapp

#
# set up emails sync cronjob
#

cat > "${basedir}/sync.sh" << EOF
#!/usr/bin/env sh

sync_secret="$(grep 'OPWEN_ADMIN_SECRET' "${basedir}/secrets.env" | cut -d'=' -f2)"

$(which curl) "http://localhost:${port}/sync?secret=\${sync_secret}"
EOF
chmod a+x "${basedir}/sync.sh"

(sudo crontab -l || true; echo "${sync_schedule} ${basedir}/sync.sh") 2>&1 | grep -v 'no crontab for' | sort -u | sudo crontab -
