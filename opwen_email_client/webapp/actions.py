from contextlib import contextmanager
from importlib import import_module
from logging import Logger
from pathlib import Path
from subprocess import check_call  # nosec
from subprocess import check_output  # nosec
from sys import executable
from time import sleep
from typing import Mapping
from typing import Optional

from cached_property import cached_property
from flask import render_template

from opwen_email_client.domain import sim
from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.domain.email.sync import Sync
from opwen_email_client.domain.email.user_store import UserStore
from opwen_email_client.domain.modem import e303
from opwen_email_client.domain.modem import e353
from opwen_email_client.domain.modem import e3131
from opwen_email_client.domain.modem import modem_is_plugged
from opwen_email_client.domain.modem import modem_is_setup
from opwen_email_client.domain.modem import setup_modem
from opwen_email_client.domain.sim import dialup
from opwen_email_client.util.os import backup
from opwen_email_client.webapp.config import i8n


class SyncEmails(object):
    def __init__(self, email_store: EmailStore, email_sync: Sync, user_store: UserStore, log: Logger):
        self._email_store = email_store
        self._email_sync = email_sync
        self._user_store = user_store
        self._log = log

    def _upload(self):
        pending = self._email_store.pending(page=None)
        users = self._user_store.fetch_pending()

        # noinspection PyBroadException
        try:
            uploaded = self._email_sync.upload(pending, users)
        except Exception:
            self._log.exception('Unable to upload emails')
        else:
            if uploaded:
                self._email_store.mark_sent(uploaded)
                self._mark_as_synced(users)

    def _mark_as_synced(self, users):
        for user in users:
            user.synced = True
            self._user_store.w.put(user)
        self._user_store.w.commit()

    def _download(self):
        # noinspection PyBroadException
        try:
            downloaded = self._email_sync.download()
        except Exception:
            self._log.exception('Unable to download emails')
        else:
            self._email_store.create(downloaded)

    def _sync(self):
        self._upload()
        self._download()

    def __call__(self):
        self._sync()


class UpdateCode(object):
    _package_name = 'opwen_email_client'

    def __init__(self, version: Optional[str], log: Logger):
        self._version = version
        self._log = log

    def __call__(self):
        if self._version:
            package = '{}=={}'.format(self._package_name, self._version)
            self._log.debug('Updating to version %s', self._version)
        else:
            package = self._package_name
            self._log.debug('Updating to latest version')

        stdout = check_output([executable, '-m', 'pip', 'install', '-U', package])

        self._log.debug('Pip install log: %s', stdout)


class RestartApp(object):
    def __init__(self, restart_paths: Mapping[str, str]):
        self._restart_paths = restart_paths

    def __call__(self):
        for path, signal in self._restart_paths.items():
            path = Path(path)
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(signal, encoding='ascii')


class RestartAppComponent(object):
    def __init__(self, restart_path: str):
        self._restart_path = restart_path

    def __call__(self):
        path = Path(self._restart_path)

        if not path.is_file():
            return

        component_name = path.name
        signal = path.read_text(encoding='ascii').strip()

        if signal:
            check_call(['supervisorctl', 'signal', signal, component_name])
        else:
            check_call(['supervisorctl', 'restart', component_name])

        path.unlink()


class SendWelcomeEmail(object):
    def __init__(self, to: str, time, email_store: EmailStore):
        self._to = to
        self._time = time
        self._email_store = email_store

    def __call__(self, *args, **kwargs):
        email_body = render_template('emails/account_finalized.html', email=self._to)
        self._email_store.create([{
            'sent_at': self._time.strftime("%Y-%m-%d %H:%M"),
            'to': [self._to],
            'from': 'info@ascoderu.ca',
            'subject': i8n.WELCOME,
            'body': email_body,
        }])


class StartInternetConnection(object):
    _supported_modems = (e303, e353, e3131)

    def __init__(self, modem_config_dir: str, sim_config_dir: str, sim_type: str, state_dir: str):
        self._modem_config_dir = Path(modem_config_dir)
        self._sim_config_dir = Path(sim_config_dir)
        self._sim_type = sim_type
        self._state_dir = Path(state_dir)
        self._modem_target_mode = '1506'

    @cached_property
    def _wvdial_config(self) -> Path:
        wvdial_config = self._sim_config_dir / self._sim_type
        if wvdial_config.is_file():
            return wvdial_config

        sim_config_module = '{}.{}'.format(sim.__name__, self._sim_type)
        try:
            sim_config = import_module(sim_config_module)
        except ImportError:
            raise Exception('SIM config {} does not exist'.format(wvdial_config))
        else:
            wvdial_config.parent.mkdir(parents=True, exist_ok=True)
            with wvdial_config.open('w', encoding='utf-8') as fobj:
                fobj.write(sim_config.wvdial)

        return wvdial_config

    @property
    def _wvdial_log(self) -> Path:
        wvdial_log = self._state_dir / 'wvdial.log'

        backup(wvdial_log)

        wvdial_log.write_bytes(b'')
        return wvdial_log

    def _modem_config_for(self, modem) -> Path:
        modem_config = self._modem_config_dir / modem.uid
        if modem_config.is_file():
            return modem_config

        modem_config.parent.mkdir(parents=True, exist_ok=True)
        with modem_config.open('w', encoding='utf-8') as fobj:
            fobj.write(modem.modeswitch)

        return modem_config

    def _setup_modem(self, poll_seconds: int):
        if not modem_is_plugged():
            raise Exception('No modem plugged in')

        if not modem_is_setup(self._modem_target_mode):
            for modem in self._supported_modems:
                if modem_is_plugged(modem):
                    self._modem_target_mode = modem.target
                    setup_modem(self._modem_config_for(modem))
                    break
            else:
                raise Exception('Unknown modem')

            while not modem_is_setup(self._modem_target_mode):
                sleep(poll_seconds)

    @contextmanager
    def __call__(self):
        connection = None

        if self._sim_type != 'Ethernet':
            self._setup_modem(poll_seconds=2)

            connection = dialup(
                self._wvdial_config,
                self._wvdial_log,
                max_retries=90,
                poll_seconds=1,
            )

        try:
            yield
        finally:
            if connection is not None:
                connection.terminate()
