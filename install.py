#!/usr/bin/env python3
"""Script to set up a Debian Linux based system as a Lokole client."""
from argparse import ArgumentParser
from base64 import b64encode
from json import dumps
from json import loads
from logging import StreamHandler
from logging import getLogger
from multiprocessing import cpu_count
from os import chmod
from os import getenv
from os import stat
from os import urandom
from pathlib import Path
from shutil import chown
from socket import gethostname
from stat import S_IEXEC
from string import ascii_letters
from string import digits
from subprocess import PIPE  # nosec
from subprocess import run  # nosec
from sys import executable as current_python_binary
from sys import version_info
from tempfile import gettempdir
from time import sleep
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

        if sudo_user and base_user == 'root':
            return sudo_user
        elif base_user:
            return base_user
        else:
            return self.sh('whoami')

    @property
    def home(self):
        return Path('/') / 'home' / self.user

    def __call__(self):
        try:
            result = self.__is_complete()
        except FileNotFoundError:
            pass
        else:
            LOG.info('Skipping %s: already completed', self._step_name)
            return result

        if not self.is_enabled:
            LOG.info('Skipping %s: not enabled', self._step_name)
            return

        LOG.info('Running %s', self._step_name)

        self._grant_permissions()
        self._install_dependencies()
        result = self._run()
        self.__mark_complete(result)

        LOG.info('Done with %s', self._step_name)
        return result

    def _grant_permissions(self):
        for group in self.groups:
            self.sh('usermod -a -G "{group}" "{user}"'
                    .format(group=group, user=self.user))

    def _install_dependencies(self):
        if self.packages:
            self.sh('apt-get install -y {}'.format(' '.join(self.packages)),
                    retry_attempts=10, retry_interval=60)

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
    def __stdout_path(self):
        stdout_name = '{}.stdout'.format(self._step_name)
        return self.abspath(TEMP_ROOT / stdout_name)

    @property
    def __stderr_path(self):
        stderr_name = '{}.stderr'.format(self._step_name)
        return self.abspath(TEMP_ROOT / stderr_name)

    def __is_complete(self):
        return loads(Path(self.__guard_path).read_text(encoding='utf-8'))

    def __mark_complete(self, result):
        self.write_file(self.__guard_path, dumps(result))

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

    def create_daemon(self, program_name, command, user=None, env=None):
        env = env or {}
        user = user or self.user
        extra_conf = []

        if self.args.log_directory == '-':
            stderr = '/dev/fd/2'
            stdout = '/dev/fd/1'
            extra_conf.extend((
                'stdout_logfile_maxbytes=0',
                'stderr_logfile_maxbytes=0',
            ))
        else:
            stderr = self.abspath(Path(self.args.log_directory) / '{}.stderr.log'.format(program_name))
            stdout = self.abspath(Path(self.args.log_directory) / '{}.stdout.log'.format(program_name))

        self.write_file('/etc/supervisor/conf.d/{}.conf'.format(program_name), (
            '[program:{}]'.format(program_name),
            'command={}'.format(command),
            'autostart=true',
            'autorestart=true',
            'startretries=3',
            'stopasgroup=true',
            'stderr_logfile={}'.format(stderr),
            'stdout_logfile={}'.format(stdout),
            'user={}'.format(user),
            'environment={}'.format(','.join('{}={}'.format(*kv) for kv in env.items())),
            *extra_conf,
        ))

    def abspath(self, file_path):
        file_path = Path(file_path).absolute()
        self._mkdir(file_path.parent)
        return str(file_path)

    def sh(self, command, user=None, accept_failure=False, retry_attempts=0, retry_interval=0):
        if user:
            command = "su '{user}' -c '{command}'".format(
                user=user,
                command=command)

        process = run(command, shell=True, stderr=PIPE, stdout=PIPE)  # nosec
        stdout = process.stdout.decode('utf-8').strip()
        stderr = process.stderr.decode('utf-8').strip()
        status = process.returncode

        with open(self.__stdout_path, 'a', encoding='utf-8') as fobj:
            fobj.write('===== {} =====\n{}\n{}\n\n'.format(command, status, stdout))

        with open(self.__stderr_path, 'a', encoding='utf-8') as fobj:
            fobj.write('===== {} =====\n{}\n{}\n\n'.format(command, status, stderr))

        if status == 0 or accept_failure:
            return stdout

        if retry_attempts > 0:
            sleep(retry_interval)
            return self.sh(command, user, accept_failure, retry_attempts - 1, retry_interval)

        raise Exception(stderr)

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
        self._ensure_root()
        self._ensure_apt()
        self._set_locale()
        self._set_timezone()
        self._set_password()

    def _ensure_root(self):
        if getenv('USER') != 'root' and self.sh('whoami') != 'root':
            self.abort('Must run script via sudo')

    def _ensure_apt(self):
        self.sh('apt-get update', retry_attempts=10, retry_interval=30)

    def _set_locale(self):
        locale_command = (
            'export LANGUAGE="{0}"; '
            'export LC_ALL="{0}"; '
            'export LANG="{0}"; '
            'export LC_TYPE="{0}";'
        ).format(self.args.locale)

        self.sh('locale-gen "{}"'.format(self.args.locale))
        self.sh('update-locale')
        self.sh('eval "{}"'.format(locale_command))

        self.write_file('/etc/profile.d/set-locale.sh', locale_command,
                        executable=True)

    def _set_timezone(self):
        self.sh('timedatectl set-timezone "{}"'.format(self.args.timezone))

    def _set_password(self):
        if not self.args.password:
            return

        self.sh('echo "{user}:{password}" | chpasswd'.format(
                user=self.user,
                password=self.args.password))

    @property
    def is_enabled(self):
        return self.args.system_setup != 'no'


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

        self.sh('systemctl unmask hostapd.service')
        self.sh('systemctl start hostapd.service')

    def _disable_system_power_management(self):
        self.sh('systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target')

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


class ModemSetup(Setup):
    packages = (
        'usb-modeswitch',
        'usb-modeswitch-data',
        'mobile-broadband-provider-info',
        'ppp',
        'wvdial',
    )

    groups = (
        'dialout',
        'dip',
    )

    def _run(self):
        self._configure_wvdial()

        return {
            'OPWEN_SYNC_SCHEDULE': self.args.sync_schedule,
        }

    def _configure_wvdial(self):
        self.write_file('/etc/ppp/peers/wvdial', (
            'noauth',
            'name wvdial',
            'usepeerdns',
            'defaultroute',
            'replacedefaultroute',
        ))

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
        request_auth = b64encode(self.args.registration_credentials.encode('ascii')).decode('ascii')

        create_request_payload = dumps({'domain': self.client_domain}).encode('utf-8')
        create_request = Request(self.client_url_create)
        create_request.add_header('Content-Type', 'application/json; charset=utf-8')
        create_request.add_header('Content-Length', str(len(create_request_payload)))
        create_request.add_header('Authorization', 'Basic {}'.format(request_auth))

        try:
            with urlopen(create_request, create_request_payload):  # nosec
                pass
        except HTTPError as ex:
            self.abort('Unable to register client {client_name}: [{status_code}] {message}'.format(
                client_name=self.args.client_name,
                status_code=ex.code,
                message=ex.read().decode('utf-8').strip()))

        while True:
            get_request = Request(self.client_url_details)
            get_request.add_header('Authorization', 'Basic {}'.format(request_auth))
            try:
                with urlopen(get_request) as response:  # nosec
                    response_body = response.read().decode('utf-8')
            except HTTPError as ex:
                if ex.code != 404:
                    self.abort('Unable to fetch client {client_name}: [{status_code}] {message}'.format(
                        client_name=self.args.client_name,
                        status_code=ex.code,
                        message=ex.read().decode('utf-8').strip()))
                sleep(2)
            else:
                client_info = loads(response_body)
                break

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
    def client_url_create(self):
        return 'https://{}/api/email/register/'.format(self.args.server_host)

    @property
    def client_url_details(self):
        return 'https://{}/api/email/register/{}'.format(self.args.server_host, self.client_domain)

    @property
    def is_enabled(self):
        return self.args.sim_type != 'LocalOnly'


class WebappSetup(Setup):
    packages = (
        'bcrypt',
        'libffi-dev',
        'libssl-dev',
        'libjpeg-dev',
        'libopenjp2-7',
        'libtiff5',
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
        self._setup_cron()
        self._setup_restarter()
        self._reboot()

    def _create_virtualenv(self):
        self.sh('{python} -m venv "{venv_path}"'.format(
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
        self.sh('"{pybabel}" compile -d "{translations}"'.format(
               pybabel='{}/bin/pybabel'.format(self.venv_path),
               translations=self.abspath(self.webapp_files_root / 'translations')),
              user=self.user)

    def _setup_secrets(self):
        extra_settings = {
            'OPWEN_APP_ROOT': self.args.app_root,
            'OPWEN_STATE_DIRECTORY': self.abspath(self.args.state_directory),
            'OPWEN_SESSION_KEY': generate_secret(32),
            'OPWEN_MAX_UPLOAD_SIZE_MB': self.args.max_upload_size,
            'OPWEN_SIM_TYPE': self.args.sim_type,
            'OPWEN_EMAIL_SERVER_HOSTNAME': self.args.server_host,
            'OPWEN_CLIENT_NAME': self.args.client_name,
            'OPWEN_ROOT_DOMAIN': self.args.client_domain,
            'OPWEN_RESTART_PATH': ','.join((
                '{}=HUP'.format(self.abspath(self.restarter_directory / self.args.server_name)),
                '{}='.format(self.abspath(self.restarter_directory / self.args.worker_name)),
                '{}='.format(self.abspath(self.restarter_directory / self.args.cron_name)),
            )),
        }

        self.write_file(self.settings_path, (
            '{}={}'.format(key, value)
            for settings in (extra_settings, self.app_config)
            for (key, value) in settings.items()))

    def _create_admin_user(self):
        if self.args.admin == 'no':
            return

        self.sh('OPWEN_SETTINGS="{settings}" '
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

              location = {app_root}/favicon.ico {{
                alias {files_root}/static/favicon.ico;
              }}

              location ~ ^{app_root}/static/(.*)$ {{
                alias {files_root}/static/$1;
              }}

              location {app_root}/ {{
                include proxy_params;
                proxy_pass http://unix:{socket};
              }}
            }}'''.format(
            port=self.args.port,
            app_root=self.args.app_root,
            files_root=self.abspath(self.webapp_files_root),
            socket=self.socket_path))

        if self.args.log_directory == '-':
            access_log = 'stdout'
            error_log = 'stderr'
        else:
            access_log = self.abspath(Path(self.args.log_directory) / 'nginx_access.log')
            error_log = self.abspath(Path(self.args.log_directory) / 'nginx_error.log')

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
              client_max_body_size {max_upload_size}M;
              include /etc/nginx/conf.d/*.conf;
              include /etc/nginx/sites-enabled/*;

              fastcgi_connect_timeout {timeout_seconds};
              fastcgi_send_timeout {timeout_seconds};
              fastcgi_read_timeout {timeout_seconds};
            }}'''.format(
            access_log=access_log,
            error_log=error_log,
            max_upload_size=self.args.max_upload_size,
            timeout_seconds=self.args.timeout))

        self.sh('systemctl stop nginx', accept_failure=True)
        self.sh('systemctl disable nginx', accept_failure=True)

        self.create_daemon(
            program_name=self.args.nginx_name,
            command='/usr/sbin/nginx -g "daemon off;"',
            user='root')

    def _setup_gunicorn(self):
        gunicorn_script = (
            '"{venv}/bin/gunicorn" '
            '--bind="unix:{socket}" '
            '--timeout={timeout} '
            '--workers={workers} '
            '--log-level={loglevel} '
            'opwen_email_client.webapp:app'.format(
                venv=self.venv_path,
                socket=self.socket_path,
                timeout=self.args.timeout,
                workers=self.args.num_gunicorn_workers,
                loglevel=self.args.log_level))

        self.create_daemon(
            program_name=self.args.server_name,
            command=gunicorn_script,
            env={'OPWEN_SETTINGS': self.settings_path})

    def _setup_celery(self):
        celery_command = (
            '"{venv}/bin/celery" '
            '--app=opwen_email_client.webapp.tasks '
            'worker '
            '--loglevel={loglevel} '
            '--concurrency={workers}'.format(
                venv=self.venv_path,
                loglevel=self.args.log_level,
                workers=self.args.num_celery_workers))

        self.create_daemon(
            program_name=self.args.worker_name,
            command=celery_command,
            env={'OPWEN_SETTINGS': self.settings_path})

    def _setup_cron(self):
        celery_command = (
            '"{venv}/bin/celery" '
            '--app=opwen_email_client.webapp.tasks '
            'beat '
            '--pidfile="{cronstate_pid}" '
            '--loglevel={loglevel} '.format(
                settings=self.settings_path,
                cronstate_pid=self.cronstate_pid,
                venv=self.venv_path,
                loglevel=self.args.log_level))

        self.create_daemon(
            program_name=self.args.cron_name,
            command=celery_command,
            env={'OPWEN_SETTINGS': self.settings_path})

    def _setup_restarter(self):
        restarter_command = (
            '"{venv}/bin/manage.py" '
            'restarter '
            '--directory="{directory}"'.format(
                venv=self.venv_path,
                directory=self.abspath(self.restarter_directory)))

        self.create_daemon(
            program_name=self.args.restarter_name,
            command=restarter_command,
            user='root')

    def _reboot(self):
        LOG.info('All done. Lokole client %s is ready to be used.', self.args.client_name)

        if self.args.reboot == 'yes':
            LOG.info('System is rebooting.')
            self.sh('shutdown --reboot now', user='root')

    def _pip_install(self, *packages):
        self.sh('"{pip}" install --no-cache-dir --upgrade {packages}'.format(
                 pip='{}/bin/pip'.format(self.venv_path),
                 packages=' '.join(packages)),
                retry_attempts=60,
                retry_interval=5,
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
        return self.abspath(Path(self.args.state_directory)
                            / '{}.sock'.format(self.args.server_name))

    @property
    def settings_path(self):
        return self.abspath(Path(self.args.state_directory)
                            / 'settings.env')

    @property
    def cronstate_pid(self):
        return self.abspath(Path(self.args.state_directory)
                            / '{}.pid'.format(self.args.cron_name))

    @property
    def restarter_directory(self):
        return Path(self.args.state_directory) / self.args.restarter_name

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
    LOG.setLevel(args.script_log_level)
    LOG.addHandler(StreamHandler())

    _dump_state(args)

    app_config = {}

    system_setup = SystemSetup(args, abort)
    system_setup()

    wifi_setup = WifiSetup(args, abort)
    wifi_setup()

    modem_setup = ModemSetup(args, abort)
    app_config.update(modem_setup() or {})

    client_setup = ClientSetup(args, abort)
    app_config.update(client_setup() or {})

    webapp_setup = WebappSetup(args, abort, app_config)
    webapp_setup()


def cli():
    parser = ArgumentParser(description=__doc__)

    parser.add_argument('client_name', type=str.lower, help=(
        'The name that should be assigned to the Lokole device '
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
    parser.add_argument('--app_root', default=getenv('OPWEN_APP_ROOT', ''), help=(
        'The URL prefix at which the app will be accessible.'
    ))
    parser.add_argument('--admin', default=getenv('LOKOLE_ADMIN', 'yes'), help=(
        'If set to "no", skip creation of application admin user.'
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
    parser.add_argument('--system_setup', default=getenv('LOKOLE_SYSTEM_SETUP', 'yes'), help=(
        'If set to "no", skip system setup.'
    ))
    parser.add_argument('--reboot', default=getenv('LOKOLE_REBOOT', 'yes'), help=(
        'If set to "no", skip system reboot after setup.'
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
    parser.add_argument('--script_log_level', default=getenv('LOKOLE_SCRIPT_LOG_LEVEL', 'INFO'), help=(
        'The logging verbosity of this script.'
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
    parser.add_argument('--server_name', default=getenv('LOKOLE_SERVER_NAME', 'lokole_gunicorn'), help=(
        'Name of the Lokole webapp server.'
    ))
    parser.add_argument('--nginx_name', default=getenv('LOKOLE_NGINX_NAME', 'lokole_nginx'), help=(
        'Name of the Nginx service.'
    ))
    parser.add_argument('--worker_name', default=getenv('LOKOLE_WORKER_NAME', 'lokole_celery_worker'), help=(
        'Name of the Lokole webapp worker.'
    ))
    parser.add_argument('--cron_name', default=getenv('LOKOLE_CRON_NAME', 'lokole_celery_beat'), help=(
        'Name of the Lokole cron worker.'
    ))
    parser.add_argument('--restarter_name', default=getenv('LOKOLE_RESTARTER_NAME', 'lokole_restarter'), help=(
        'Name of the Lokole restarter.'
    ))
    parser.add_argument('--log_level', default=getenv('LOKOLE_LOG_LEVEL', 'error'), help=(
        'The log level for the Lokole email app.'
    ))
    parser.add_argument('--timeout', type=int, default=300, help=(
        'Timeout for the Lokole email app. In seconds.'
    ))
    parser.add_argument('--max_upload_size', type=int, default=10, help=(
        'Maximum allowed size of uploads to the Lokole email app. In MB.'
    ))
    parser.add_argument('--num_celery_workers', type=int, default=2, help=(
        'Number of celery workers for the Lokole email app.'
    ))
    parser.add_argument('--num_gunicorn_workers', type=int, default=max(2, cpu_count() - 1), help=(
        'Number of gunicorn workers for the Lokole email app.'
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
