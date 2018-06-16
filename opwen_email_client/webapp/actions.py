from logging import Logger

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
