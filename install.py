#!/usr/bin/env python3
"""Script to set up a Debian Linux based system as a Lokole client."""
from argparse import ArgumentParser
from base64 import b64encode
from datetime import datetime
from json import dumps
from json import loads
from logging import getLogger
from os import chmod
from os import getenv
from os import stat
from os import sysconf
from os import urandom
from pathlib import Path
from shutil import chown
from socket import gethostname
from stat import S_IEXEC
from string import ascii_letters
from string import digits
from subprocess import check_call  # nosec
from sys import executable as current_python_binary
from sys import version_info
from tempfile import gettempdir
from time import time
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen

LOG = getLogger(__name__)

TEMP_ROOT = Path(gettempdir()) / Path(__file__).name
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

SIM_TYPES = ('hologram', 'Ethernet', 'LocalOnly', 'mkwvconf')


class Setup:
    groups = tuple()
    packages = tuple()

    def __init__(self, args, abort):
        self.args = args
        self.abort = abort

    @property
    def is_enabled(self):
        return True

    @property
    def user(self):
        base_user = getenv('USER')
        sudo_user = getenv('SUDO_USER')
        return sudo_user if sudo_user and base_user == 'root' else base_user

    @property
    def home(self):
        return Path('/') / 'home' / self.user

    def __call__(self):
        if self.__is_complete:
            LOG.info('Skipping %s: already completed', self._step_name)
            return

        if not self.is_enabled:
            LOG.info('Skipping %s: not enabled', self._step_name)
            return

        self._grant_permissions()
        self._install_dependencies()
        result = self._run()
        self.__mark_complete()

        LOG.info('Done with %s', self._step_name)
        return result

    def _grant_permissions(self):
        for group in self.groups:
            sh('usermod -a -G "{group}" "{user}"'
               .format(group=group, user=self.user))

    def _install_dependencies(self):
        sh('apt-get install -y {}'.format(' '.join(self.packages)))

    def _run(self):
        raise NotImplementedError

    @property
    def _step_name(self):
        return self.__class__.__name__

    @property
    def __guard_path(self):
        guard_name = '{}.done'.format(self._step_name)
        return self.abspath(TEMP_ROOT / guard_name)

    @property
    def __is_complete(self):
        return Path(self.__guard_path).is_file()

    def __mark_complete(self):
        self.write_file(self.__guard_path, str(datetime.now()))

    def assume_ownership(self, path):
        chown(path, self.user, self.user)

    def write_file(self, path, content, executable=False):
        if not isinstance(content, str):
            content = '\n'.join(content)

        with open(path, 'w') as fobj:
            fobj.write(content)

        self.assume_ownership(path)

        if executable:
            mode = stat(path).st_mode
            chmod(path, mode | S_IEXEC)

    def create_daemon(self, program_name, command, user=None):
        stderr = self.abspath(Path(self.args.log_directory) / '{}.stderr.log'.format(program_name))
        stdout = self.abspath(Path(self.args.log_directory) / '{}.stdout.log'.format(program_name))

        script_path = self.abspath(Path(self.args.scripts_directory) / '{}.sh'.format(program_name))
        self.write_file(script_path, '#!/usr/bin/env sh\n\n{}'.format(command), executable=True)

        self.write_file('/etc/supervisor/conf.d/{}.conf'.format(program_name), (
            '[program:{}]'.format(program_name),
            'command={}'.format(script_path),
            'autostart=true',
            'autorestart=true',
            'startretries=3',
            'stderr_logfile={}'.format(stderr),
            'stdout_logfile={}'.format(stdout),
            'user={}'.format(user or self.user),
        ))

        sh('service supervisor start; '
           'supervisorctl reread; '
           'supervisorctl update;')

    def create_cronjob(self, schedule, command):
        sh('(crontab -l -u {user} || true; echo "{schedule} {command}") 2>&1 '
           '| grep -v "no crontab for" '
           '| sort -u '
           '| crontab -u {user} -'
           .format(schedule=schedule, command=command, user=self.user))

    def abspath(self, file_path):
        file_path = Path(file_path).absolute()
        self._mkdir(file_path.parent)
        return str(file_path)

    def _mkdir(self, path):
        path.mkdir(parents=True, exist_ok=True)
        home_prefix = Path(self.home)
        is_in_home = path.parts[:3] == home_prefix.parts
        if is_in_home:
            home_parts = path.parts[3:]
            for part in home_parts:
                home_prefix /= part
                self.assume_ownership(str(home_prefix))


class SystemSetup(Setup):
    def _run(self):
        self._update_apt()
        self._set_locale()
        self._set_timezone()
        self._set_password()

    def _update_apt(self):
        sh('apt-get update')

    def _set_locale(self):
        locale_command = (
            'export LANGUAGE="{0}"; '
            'export LC_ALL="{0}"; '
            'export LANG="{0}"; '
            'export LC_TYPE="{0}";'
        ).format(self.args.locale)

        sh('locale-gen "{}"'.format(self.args.locale))
        sh('update-locale')
        sh('eval "{}"'.format(locale_command))

        self.write_file('/etc/profile.d/set-locale.sh', locale_command,
                        executable=True)

    def _set_timezone(self):
        sh('timedatectl set-timezone "{}"'.format(self.args.timezone))

    def _set_password(self):
        if not self.args.password:
            return

        sh('echo "{user}:{password}" | chpasswd'.format(
            user=self.user,
            password=self.args.password))


class WifiSetup(Setup):
    packages = (
        'hostapd',
        'dnsmasq',
    )

    ip_base = '10.0.0'

    def _run(self):
        if not self.ht_capab:
            self.abort('Unsupported device: {}'.format(self.device))

        self._configure_dns()
        self._configure_wifi()
        self._disable_system_power_management()

    def _configure_dns(self):
        hosts = [
            ('::1', 'localhost ip6-localhost ip6-loopback'),
            ('ff02::1', 'ip6-allnodes'),
            ('ff02::2', 'ip6-allrouters'),
            ('127.0.0.1', 'localhost'),
            ('127.0.0.1', self.device),
            ('127.0.1.1', self.device),
        ]

        for prefix in ['www.', '']:
            for tld in ['.com', '.org', '.ca', '.cd', '']:
                for host in ['lokole', 'opwen', 'ascoderu', 'email']:
                    hosts.append((self.ip, prefix + host + tld))

        self.write_file('/etc/hosts', ('{}\t{}'.format(ip, host) for (ip, host) in hosts))

        logfile = '/var/log/dnsmasq.log'

        self.write_file('/etc/dnsmasq.conf', (
            'log-facility={}'.format(logfile),
            'dhcp-range={0}.10,{0}.250,12h'.format(self.ip_base),
            'interface=wlan0',
            'no-resolv',
            'log-queries',
            'server=8.8.8.8',
        ))

    def _configure_wifi(self):
        hostapd_conf = '/etc/hostapd/hostapd.conf'

        self.write_file(hostapd_conf, (
            'interface=wlan0',
            'driver=nl80211',
            'hw_mode=g',
            'channel=6',
            'ieee80211n=1',
            'wmm_enabled=1',
            'ht_capab={}'.format(self.ht_capab),
            'macaddr_acl=0',
            'auth_algs=1',
            'wpa=2',
            'wpa_key_mgmt=WPA-PSK',
            'rsn_pairwise=CCMP',
            'ssid={}'.format(self.args.wifi_name),
            'wpa_passphrase={}'.format(self.args.wifi_password),
        ))

        self.write_file('/etc/default/hostapd', 'DAEMON_CONF={}'.format(hostapd_conf))

        self.write_file('/etc/network/interfaces', (
            'auto lo',
            'iface lo inet loopback',

            'auto eth0',
            'allow-hotplug eth0',
            'iface eth0 inet dhcp',

            'auto wlan0',
            'allow-hotplug wlan0',
            'iface wlan0 inet static',
            'post-up service hostapd restart',
            'post-up service dnsmasq restart',
            'address {}'.format(self.ip),
            'netmask 255.255.255.0',
            'wireless-power off',

            'auto ppp0',
            'iface ppp0 inet wvdial',
        ))

        sh('systemctl unmask hostapd.service')
        sh('systemctl start hostapd.service')

    def _disable_system_power_management(self):
        sh('systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target')

    @property
    def ip(self):
        return '{}.1'.format(self.ip_base)

    @property
    def device(self):
        return gethostname()

    @property
    def ht_capab(self):
        if self.device in ['OrangePI', 'orangepizero']:
            return '[HT40][DSS_CCK-40]'

        if self.device in ['raspberrypi']:
            return '[HT40][SHORT-GI-20][DSS_CCK-40]'

        return None

    @property
    def is_enabled(self):
        return self.args.wifi != 'no'


class SyncSetup(Setup):
    packages = (
        'cron',
        'usb-modeswitch',
        'usb-modeswitch-data',
        'mobile-broadband-provider-info',
        'ppp',
        'wvdial',
    )

    groups = (
        'crontab',
        'dialout',
        'dip',
    )

    def _run(self):
        self._configure_wvdial()
        self._configure_webapp_sync()

        return {
            'OPWEN_SYNC_SCRIPT': self.sync_script,
            'OPWEN_ADMIN_SECRET': self.admin_secret,
        }

    def _configure_wvdial(self):
        self.write_file('/etc/ppp/peers/wvdial', (
            'noauth',
            'name wvdial',
            'usepeerdns',
            'defaultroute',
            'replacedefaultroute',
        ))

    def _configure_webapp_sync(self):
        self.create_cronjob(self.args.sync_schedule, self.sync_script)

    @property
    def admin_secret(self):
        try:
            return getattr(self, '__admin_secret')
        except AttributeError:
            admin_secret = generate_secret(32)
            setattr(self, '__admin_secret', admin_secret)
            return admin_secret

    @property
    def sync_script(self):
        try:
            return getattr(self, '__sync_script')
        except AttributeError:
            sync_script_path = self.abspath(Path(self.args.scripts_directory) / 'sync.sh')
            stderr = self.abspath(Path(self.args.log_directory) / 'sync.stderr.log')

            sync_command = (
                '#!/usr/bin/env sh\n\n'
                'curl -LfsS "http://localhost:{port}/admin/sync?secret={secret}" 2>>"{stderr}" >/dev/null'
            ).format(port=self.args.port, secret=self.admin_secret, stderr=stderr)

            self.write_file(sync_script_path, sync_command, executable=True)

            setattr(self, '__sync_script', sync_script_path)
            return sync_script_path

    @property
    def is_enabled(self):
        if not super().is_enabled:
            return False

        if self.args.sim_type == 'LocalOnly':
            return False

        if not self.args.sync_schedule or not self.args.registration_credentials:
            self.abort('Sync schedule and registration credentials are required.')

        return True


class ClientSetup(Setup):
    def _run(self):
        request_payload = dumps({'domain': self.client_domain}).encode('utf-8')
        request_auth = b64encode(self.args.registration_credentials.encode('ascii')).decode('ascii')

        request = Request(self.registration_url)
        request.add_header('Content-Type', 'application/json; charset=utf-8')
        request.add_header('Content-Length', len(request_payload))
        request.add_header('Authorization', 'Basic {}'.format(request_auth))

        try:
            with urlopen(request, request_payload) as response:  # nosec
                response_body = response.read().decode('utf-8')
        except HTTPError as ex:
            self.abort('Unable to register client {client_name}: [{status_code}] {message}'.format(
                client_name=self.args.client_name,
                status_code=ex.code,
                message=ex.read().decode('utf-8').strip()))
        else:
            client_info = loads(response_body)
            return {
                'OPWEN_CLIENT_ID': client_info['client_id'],
                'OPWEN_REMOTE_ACCOUNT_NAME': client_info['storage_account'],
                'OPWEN_REMOTE_ACCOUNT_KEY': client_info['storage_key'],
                'OPWEN_REMOTE_RESOURCE_CONTAINER': client_info['resource_container'],
            }

    @property
    def client_domain(self):
        return '{}.{}'.format(self.args.client_name, self.args.client_domain)

    @property
    def registration_url(self):
        return 'https://{}/api/email/register/'.format(self.args.server_host)


class RestartSetup(Setup):
    packages = (
        'inotify-tools',
        'supervisor',
    )

    def _run(self):
        daemon_name = 'restarter'

        restart_directory = Path(self.args.state_directory) / daemon_name

        restart_daemon = (
            'inotifywait --format "%f" --event create --monitor "{restart_directory}" '
            '| while read -r service; do '
            'test -n "$service" && '
            'test -f "{restart_directory}/$service" && '
            'supervisorctl restart "$service" >/dev/null && '
            'rm -f "{restart_directory}/$service" '
            '; done'
        ).format(restart_directory=self.abspath(restart_directory))

        self.create_daemon(
            program_name=daemon_name,
            command=restart_daemon,
            user='root')

        return {
            'OPWEN_RESTART_PATH': ','.join((
                self.abspath(restart_directory / self.args.server_name),
                self.abspath(restart_directory / self.args.worker_name),
            )),
        }


class WebappSetup(Setup):
    packages = (
        'bcrypt',
        'libffi-dev',
        'libssl-dev',
        'nginx',
        'python3',
        'python3-dev',
        'python3-pip',
        'python3-venv',
        'supervisor',
    )

    def __init__(self, args, abort, app_config):
        super().__init__(args, abort)
        self.app_config = app_config

    def _run(self):
        self._create_virtualenv()
        self._install_client()
        self._compile_translations()
        self._setup_secrets()
        self._create_admin_user()
        self._install_nginx()
        self._setup_gunicorn()
        self._setup_celery()

    def _create_virtualenv(self):
        sh('{python} -m venv "{venv_path}"'.format(
            python=current_python_binary,
            venv_path=self.venv_path),
           user=self.user)

        self._pip_install('pip', 'setuptools', 'wheel')

    def _install_client(self):
        if self.args.client_dist and Path(self.args.client_dist).is_file():
            package = self.args.client_dist
        elif self.args.client_version:
            package = 'opwen_email_client=={}'.format(self.args.client_version)
        else:
            package = 'opwen_email_client'

        self._pip_install(package)

    def _compile_translations(self):
        sh('"{pybabel}" compile -d "{translations}"'.format(
            pybabel='{}/bin/pybabel'.format(self.venv_path),
            translations=self.abspath(self.webapp_files_root / 'translations')),
           user=self.user)

    def _setup_secrets(self):
        extra_settings = {
            'OPWEN_STATE_DIRECTORY': self.abspath(self.args.state_directory),
            'OPWEN_SESSION_KEY': generate_secret(32),
            'OPWEN_PASSWORD_SALT': generate_secret(16),
            'OPWEN_SIM_TYPE': self.args.sim_type,
            'OPWEN_EMAIL_SERVER_HOSTNAME': self.args.server_host,
            'OPWEN_CLIENT_NAME': self.args.client_name,
            'OPWEN_ROOT_DOMAIN': self.args.client_domain,
        }

        self.write_file(self.settings_path, (
            '{}={}'.format(key, value)
            for settings in (extra_settings, self.app_config)
            for (key, value) in settings.items()))

    def _create_admin_user(self):
        sh('OPWEN_SETTINGS="{settings}" '
           '"{manage}" createadmin --name="{name}" --password="{password}"'.format(
            settings=self.settings_path,
            manage='{}/bin/manage.py'.format(self.venv_path),
            name=self.args.admin_name,
            password=self.args.admin_password),
           user=self.user)

    def _install_nginx(self):
        self.write_file('/etc/nginx/sites-available/default', '''
            server {{
              listen {port};
              server_name localhost;

              location = /favicon.ico {{
                alias {app_root}/static/favicon.ico;
              }}

              location /static/ {{
                root {app_root};
              }}

              location / {{
                include proxy_params;
                proxy_pass http://unix:{socket};
              }}
            }}'''.format(
            port=self.args.port,
            app_root=self.abspath(self.webapp_files_root),
            socket=self.socket_path))

        self.write_file('/etc/nginx/nginx.conf', '''
            user www-data;
            worker_processes 4;
            pid /run/nginx.pid;

            events {{
              worker_connections 768;
            }}

            http {{
              sendfile on;
              tcp_nopush on;
              tcp_nodelay on;
              keepalive_timeout 65;
              types_hash_max_size 2048;
              include /etc/nginx/mime.types;
              default_type application/octet-stream;
              ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
              ssl_prefer_server_ciphers on;
              access_log {access_log};
              error_log {error_log};
              gzip on;
              gzip_disable "msie6";
              include /etc/nginx/conf.d/*.conf;
              include /etc/nginx/sites-enabled/*;

              fastcgi_connect_timeout {timeout_seconds};
              fastcgi_send_timeout {timeout_seconds};
              fastcgi_read_timeout {timeout_seconds};
            }}'''.format(
            access_log=self.abspath(Path(self.args.log_directory) / 'nginx_access.log'),
            error_log=self.abspath(Path(self.args.log_directory) / 'nginx_error.log'),
            timeout_seconds=self.args.timeout))

        sh('systemctl restart nginx')

    def _setup_gunicorn(self):
        system_memory = sysconf('SC_PAGE_SIZE') * sysconf('SC_PHYS_PAGES')
        possible_workers = system_memory / (self.args.memory_per_worker * (1024 ** 2))
        workers = min(possible_workers, self.args.max_workers)

        gunicorn_script = (
            'exec "{gunicorn}" '
            '--bind="unix:{socket}" '
            '--timeout={timeout} '
            '--workers={workers} '
            '--log-level={loglevel} '
            '--env "OPWEN_SETTINGS={settings}" '
            'opwen_email_client.webapp:app'.format(
                gunicorn='{}/bin/gunicorn'.format(self.venv_path),
                socket=self.socket_path,
                timeout=self.args.timeout,
                workers=workers,
                loglevel=self.args.log_level,
                settings=self.settings_path))

        self.create_daemon(
            program_name=self.args.server_name,
            command=gunicorn_script)

    def _setup_celery(self):
        celery_command = (
            'OPWEN_SETTINGS="{settings}" '
            'exec "{celery}" '
            '--app=opwen_email_client.webapp.tasks '
            'worker '
            '--loglevel={loglevel} '
            '--concurrency={workers}'.format(
                settings=self.settings_path,
                celery='{}/bin/celery'.format(self.venv_path),
                loglevel=self.args.log_level,
                workers=1))

        self.create_daemon(
            program_name=self.args.worker_name,
            command=celery_command)

    def _pip_install(self, *packages):
        sh('while ! "{pip}" install --no-cache-dir --upgrade {packages}; do sleep 2s; done'.format(
            pip='{}/bin/pip'.format(self.venv_path),
            packages=' '.join(packages)),
           user=self.user)

    @property
    def webapp_files_root(self):
        return (Path(self.venv_path) /
                'lib' /
                'python{}.{}'.format(version_info.major, version_info.minor) /
                'site-packages' /
                'opwen_email_client' /
                'webapp')

    @property
    def socket_path(self):
        return self.abspath(Path(self.args.state_directory) / 'gunicorn.sock')

    @property
    def settings_path(self):
        return self.abspath(Path(self.args.state_directory) / 'webapp_settings.env')

    @property
    def venv_path(self):
        return self.abspath(Path(self.args.venv_directory))


def generate_secret(length, chars=frozenset(ascii_letters + digits)):
    secret = ''  # nosec

    while len(secret) < length:
        for char in urandom(length).decode('ascii', errors='ignore'):
            if char in chars:
                secret += char

    return secret[:length]


def sh(command, user=None):
    if user:
        command = "su '{user}' -c '{command}'".format(
            user=user,
            command=command)

    check_call(command, shell=True)  # nosec


def _dump_state(args):
    with Path(__file__).open('r', encoding='utf-8') as fobj:
        version = hash(fobj.read())

    state_path = TEMP_ROOT / 'state_{:.0f}.json'.format(time())

    with state_path.open('w', encoding='utf-8') as fobj:
        fobj.write(dumps({
            'version': version,
            'args': args.__dict__,
        }))


def main(args, abort):
    _dump_state(args)

    app_config = {}

    system_setup = SystemSetup(args, abort)
    system_setup()

    wifi_setup = WifiSetup(args, abort)
    wifi_setup()

    sync_setup = SyncSetup(args, abort)
    app_config.update(sync_setup() or {})

    client_setup = ClientSetup(args, abort)
    app_config.update(client_setup() or {})

    restart_setup = RestartSetup(args, abort)
    app_config.update(restart_setup() or {})

    webapp_setup = WebappSetup(args, abort, app_config)
    webapp_setup()


def cli():
    parser = ArgumentParser(description=__doc__)

    parser.add_argument('client_name', type=str.lower, help=(
        'The name that should be assigned to the Opwen device '
        'that is being configured by this script. Usually this '
        'will be a name that is descriptive for the location '
        'where the device will be deployed. The client name '
        'should be globally unique as it is used as the key for '
        'a bunch of things.'
    ))
    parser.add_argument('sim_type', choices=SIM_TYPES, help=(
        'The mobile network to which to connect to upload data.'
    ))
    parser.add_argument('sync_schedule', nargs='?', help=(
        'How often the Lokole should sync with the server. '
        'In cron syntax. '
        'Example: "34 * * * *" for once per hour at the 34th minute.'
    ))
    parser.add_argument('registration_credentials', nargs='?', help=(
        'Username and password (separated by a colon ":") for '
        'registering with the Lokole server.'
    ))
    parser.add_argument('--admin_name', default=getenv('LOKOLE_ADMIN_NAME', 'admin'), help=(
        'If set, create an admin user with this account name.'
    ))
    parser.add_argument('--admin_password', default=getenv('LOKOLE_ADMIN_PASSWORD', 'lokole1Admin'), help=(
        'If set, create an admin user with this password.'
    ))
    parser.add_argument('--password', default=getenv('LOKOLE_PASSWORD', ''), help=(
        'If set to a non-empty string, updates the password of '
        'the current user to this value as part of the setup. '
        'Useful for fully automated setups of new devices that '
        'come with a default insecure password.'
    ))
    parser.add_argument('--wifi', default=getenv('LOKOLE_WIFI', 'yes'), help=(
        'If set to "no", skip setup of WiFi access point and '
        'local DNS server configuration.'
    ))
    parser.add_argument('--wifi_name', default=getenv('LOKOLE_NETWORK_NAME', 'Lokole'), help=(
        'The name of the WiFi network to create for the Lokole email app.'
    ))
    parser.add_argument('--wifi_password', default=getenv('LOKOLE_NETWORK_PASSWORD', 'Ascoderu'), help=(
        'The password of the WiFi network to create for the Lokole email app.'
    ))
    parser.add_argument('--server_host', default=getenv('LOKOLE_SERVER_HOST', 'mailserver.lokole.ca'), help=(
        'The host of the email sync server to use.'
    ))
    parser.add_argument('--client_domain', default=getenv('LOKOLE_CLIENT_DOMAIN', 'lokole.ca'), help=(
        'The root domain for which to set up the Lokole email app.'
    ))
    parser.add_argument('--client_version', default=getenv('LOKOLE_CLIENT_VERSION', ''), help=(
        'The version of the Lokole email app to install.'
    ))
    parser.add_argument('--client_dist', default=getenv('LOKOLE_CLIENT_DIST', ''), help=(
        'The dist package of the Lokole email app to install.'
    ))
    parser.add_argument('--port', default=getenv('LOKOLE_PORT', '80'), help=(
        'The port on which to run the Lokole email app.'
    ))
    parser.add_argument('--state_directory', default=getenv('LOKOLE_STATE_DIRECTORY', 'lokole/state'), help=(
        'The location where to store the Lokole email app state.'
    ))
    parser.add_argument('--log_directory', default=getenv('LOKOLE_LOG_DIRECTORY', 'lokole/logs'), help=(
        'The location where to store the Lokole email app logs.'
    ))
    parser.add_argument('--venv_directory', default=getenv('LOKOLE_VENV_DIRECTORY', 'lokole/venv'), help=(
        'The location where to store the Lokole email app Python environment.'
    ))
    parser.add_argument('--scripts_directory', default=getenv('LOKOLE_SCRIPTS_DIRECTORY', 'lokole/scripts'), help=(
        'The location where to store the Lokole email app scripts.'
    ))
    parser.add_argument('--server_name', default=getenv('LOKOLE_SERVER_NAME', 'gunicorn_server'), help=(
        'Name of the Lokole webapp server.'
    ))
    parser.add_argument('--worker_name', default=getenv('LOKOLE_WORKER_NAME', 'celery_worker'), help=(
        'Name of the Lokole webapp worker.'
    ))
    parser.add_argument('--log_level', default=getenv('LOKOLE_LOG_LEVEL', 'error'), help=(
        'The log level for the Lokole email app.'
    ))
    parser.add_argument('--timeout', type=int, default=300, help=(
        'Timeout for the Lokole email app. In seconds.'
    ))
    parser.add_argument('--max_workers', type=int, default=4, help=(
        'Number of web workers for the Lokole email app.'
    ))
    parser.add_argument('--memory_per_worker', type=int, default=20, help=(
        'Amount of memory usage estimated for each web worker. In megabytes.'
    ))
    parser.add_argument('--locale', default=getenv('LOKOLE_LOCALE', 'en_GB.UTF-8'), help=(
        'Locale to set up on the system.'
    ))
    parser.add_argument('--timezone', default=getenv('LOKOLE_TIMEZONE', 'Etc/UTC'), help=(
        'Timezone to set up on the system.'
    ))

    main(parser.parse_args(), parser.error)


if __name__ == '__main__':
    cli()
