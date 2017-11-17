#!/usr/bin/env bash

info() { echo "$@"; }
error() { echo "$@"; exit 1; }
python_version() { python3 --version 2>&1 | cut -d' ' -f2- | cut -d'.' -f1,2; }
set_locale() { sudo locale-gen "$1" && sudo update-locale; local cmd="export LANGUAGE='$1'; export LC_ALL='$1'; export LANG='$1'; export LC_TYPE='$1';"; echo "${cmd}" >> "/home/$2/.bashrc"; eval "${cmd}"; }
set_timezone() { sudo timedatectl set-timezone "$1"; }
count_to() { seq 1 "$1"; }
update_system_packages() { sudo apt-get update; sudo apt-get upgrade -y; }
install_system_package() { sudo apt-get install -y "$@"; }
remove_system_package() { sudo apt-get remove -y "$@"; }
install_python_package() { pip install "$1"; }
update_python_package() { pip install --upgrade "$1"; }
write_file() { mkdir -p "$(dirname "$1")"; sudo tee "$1" > /dev/null; }
replace_file() { sudo sed -i "$1" "$2"; }
create_file() { sudo touch "$1"; sudo chown "$2" "$1"; }
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
get_system_processors_available() { getconf _NPROCESSORS_ONLN; }
min() { if [ "$1" -lt "$2" ]; then echo "$1"; else echo "$2"; fi; }
create_root_cron() { (sudo crontab -l || true; echo "$1 $2") 2>&1 | grep -v 'no crontab for' | sort -u | sudo crontab -; }
create_cron() { (crontab -l || true; echo "$1 $2") 2>&1 | grep -v 'no crontab for' | sort -u | crontab -; }
http_delete() { /usr/bin/curl --request 'DELETE' "$@"; }
http_post_json() { /usr/bin/curl --header 'Content-Type: application/json' --request 'POST' "$@"; }
reload_daemons() { sudo service supervisor start; sudo supervisorctl reread; sudo supervisorctl update; }

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
