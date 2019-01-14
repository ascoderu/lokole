from logging import Logger
from contextlib import contextmanager
from subprocess import check_call  # nosec
from subprocess import check_output  # nosec
from subprocess import Popen  # nosec
from subprocess import CalledProcessError  # nosec
from tempfile import NamedTemporaryFile
from time import sleep

from flask import render_template

from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.domain.email.sync import Sync
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
    _internet_modem_config_e3131 = '/etc/usb_modeswitch.d/12d1:155b'
    _internet_modem_config_e303 = '/etc/usb_modeswitch.d/12d1:14fe'
    _internet_modem_config_e353 = '/etc/usb_modeswitch.d/12d1:1f01'
    _internet_dialer_config = '/etc/wvdial.conf'
    _modem_target_mode = '1506'
    _sleep_time = 1

    def __init__(self, sim_type):
        self._sim_type = sim_type

    @classmethod
    def _check_process(cls, command):
        try:
            check_call(command, shell=True)  # nosec
        except CalledProcessError:
            return False
        return True

    @classmethod
    def _check_process_output(cls, command):
        return check_output(command, shell=True)  # nosec

    @classmethod
    def _open_connection(cls, log_file):
        return Popen(['/usr/bin/wvdial',
                      '--config', cls._internet_dialer_config],
                     stderr=log_file)

    @classmethod
    def _find_device(cls, stdout, uid):
        for line in stdout.splitlines():
            if 'Huawei' not in line.decode('utf-8'):
                continue
            if uid in line.decode('utf-8'):
                return True
        return False

    def _modem_is_e303(self):
        result = self._check_process_output(['/usr/bin/lsusb'])
        return self._find_device(result, '12d1:14fe')

    def _modem_is_e353(self):
        result = self._check_process_output(['/usr/bin/lsusb'])
        return self._find_device(result, '12d1:1f01')

    def _modem_is_e3131(self):
        result = self._check_process_output(['/usr/bin/lsusb'])
        return self._find_device(result, '12d1:155b')

    def _modem_is_plugged(self):
        result = self._check_process_output(['/usr/bin/lsusb'])
        return self._find_device(result, '12d1:')

    def _modem_is_setup(self):
        result = self._check_process_output(['/usr/bin/lsusb'])
        return self._find_device(
            result,
            '12d1:{0}'.format(self._modem_target_mode))

    def _dialer_is_connected(self, log):
        return self._check_process(
            "grep 'secondary DNS address' {0}".format(log.name))

    def _setup_modem(self, config):
        self._check_process(['/usr/sbin/usb_modeswitch',
                             '--config-file', config])

    @contextmanager
    def __call__(self):
        connection = None
        retry_count = 90

        if self._sim_type != 'Ethernet':
            if not self._modem_is_plugged():
                raise Exception('No modem plugged in')

            if not self._modem_is_setup():
                if self._modem_is_e303():
                    self._modem_target_mode = '1506'
                    self._setup_modem(self._internet_modem_config_e303)
                elif self._modem_is_e353():
                    self._modem_target_mode = '1001'
                    self._setup_modem(self._internet_modem_config_e353)
                elif self._modem_is_e3131():
                    self._modem_target_mode = '1506'
                    self._setup_modem(self._internet_modem_config_e3131)
                else:
                    raise Exception('Unexpected error')

                while not self._modem_is_setup():
                    sleep(self._sleep_time)

            with NamedTemporaryFile() as wvdial_log:
                connection = self._open_connection(wvdial_log)
                while not self._dialer_is_connected(wvdial_log):
                    if retry_count <= 0:
                        connection.terminate()
                        raise Exception('Modem taking to long to connect, '
                                        'exiting...')
                    sleep(self._sleep_time)
                    retry_count -= 1

        try:
            yield
        finally:
            if connection is not None:
                connection.terminate()
