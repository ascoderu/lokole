from contextlib import contextmanager
from logging import Logger
from pathlib import Path
from time import sleep

from cached_property import cached_property
from flask import render_template

from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.domain.email.sync import Sync
from opwen_email_client.domain.modem import e303
from opwen_email_client.domain.modem import e3131
from opwen_email_client.domain.modem import e353
from opwen_email_client.domain.modem import modem_is_plugged
from opwen_email_client.domain.modem import modem_is_setup
from opwen_email_client.domain.modem import setup_modem
from opwen_email_client.domain.sim import dialup
from opwen_email_client.domain.sim import hologram
from opwen_email_client.webapp.config import i8n


class SyncEmails(object):
    def __init__(self, email_store: EmailStore, email_sync: Sync,
                 log: Logger):
        self._email_store = email_store
        self._email_sync = email_sync
        self._log = log

    def _upload(self):
        pending = self._email_store.pending()

        # noinspection PyBroadException
        try:
            uploaded = self._email_sync.upload(pending)
        except Exception:
            self._log.exception('Unable to upload emails')
        else:
            self._email_store.mark_sent(uploaded)

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


class SendWelcomeEmail(object):
    def __init__(self, to: str, time, email_store: EmailStore):
        self._to = to
        self._time = time
        self._email_store = email_store

    def __call__(self, *args, **kwargs):
        email_body = render_template('emails/account_finalized.html',
                                     email=self._to)
        self._email_store.create([{
            'sent_at': self._time.strftime("%Y-%m-%d %H:%M"),
            'to': [self._to],
            'from': 'info@ascoderu.ca',
            'subject': i8n.WELCOME,
            'body': email_body,
        }])


class StartInternetConnection(object):
    _supported_modems = (e303, e353, e3131)

    def __init__(self, modem_config_dir: str, sim_config_dir: str,
                 sim_type: str):
        self._modem_config_dir = Path(modem_config_dir)
        self._sim_config_dir = Path(sim_config_dir)
        self._sim_type = sim_type
        self._modem_target_mode = '1506'

    @cached_property
    def _wvdial_config(self) -> Path:
        wvdial_config = self._sim_config_dir / self._sim_type
        if wvdial_config.is_file():
            return wvdial_config

        if self._sim_type == 'Hologram_World':
            wvdial_config.parent.mkdir(parents=True)
            with wvdial_config.open('w', encoding='utf-8') as fobj:
                fobj.write(hologram.wvdial)
        else:
            raise Exception('SIM config {} does not exist'
                            .format(wvdial_config))

        return wvdial_config

    def _modem_config_for(self, modem) -> Path:
        modem_config = self._modem_config_dir / modem.uid
        if modem_config.is_file():
            return modem_config

        modem_config.parent.mkdir(parents=True)
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
                max_retries=90,
                poll_seconds=1)

        try:
            yield
        finally:
            if connection is not None:
                connection.terminate()
