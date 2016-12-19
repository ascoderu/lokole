from flask import render_template

from opwen_email_client.config import i8n

from opwen_infrastructure.networking import use_network_interface


class SyncEmails(object):
    def __init__(self, email_store, email_sync, internet_interface):
        """
        :type email_store: opwen_domain.email.EmailStore
        :type email_sync: opwen_domain.sync.Sync
        :type internet_interface: str

        """
        self._email_store = email_store
        self._email_sync = email_sync
        self._internet_interface = internet_interface

    def __call__(self):
        with use_network_interface(self._internet_interface):
            pending = self._email_store.pending()
            uploaded = self._email_sync.upload([pending])
            self._email_store.mark_sent(uploaded)
            self._email_store.create(self._email_sync.download())


class SendWelcomeEmail(object):
    def __init__(self, to, time, email_store):
        """
        :type to: str
        :type time: datetime.datetime
        :type email_store: opwen_domain.email.EmailStore

        """
        self._to = to
        self._time = time
        self._email_store = email_store

    def __call__(self, *args, **kwargs):
        self._email_store.create([{
            'sent_at': self._time.strftime("%Y-%m-%d %H:%M"),
            'to': [self._to],
            'from': i8n.LOKOLE_TEAM,
            'subject': i8n.WELCOME,
            'body': render_template('_account_finalized.html', email=self._to),
        }])
