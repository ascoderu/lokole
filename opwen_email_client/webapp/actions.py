from flask import render_template

from opwen_email_client.webapp.config import i8n


class SyncEmails(object):
    def __init__(self, email_store, email_sync):
        """
        :type email_store: opwen_domain.email.EmailStore
        :type email_sync: opwen_domain.sync.Sync

        """
        self._email_store = email_store
        self._email_sync = email_sync

    def _upload(self):
        pending = self._email_store.pending()
        uploaded = self._email_sync.upload([pending])
        self._email_store.mark_sent(uploaded)

    def _download(self):
        downloaded = self._email_sync.download()
        self._email_store.create(downloaded)

    def _sync(self):
        self._upload()
        self._download()

    def __call__(self):
        self._sync()


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
            'from': 'info@ascoderu.ca',
            'subject': i8n.WELCOME,
            'body': render_template('emails/account_finalized.html', email=self._to),
        }])
