import atexit
import json
from itertools import chain

from ca.ascoderu.lokole.domain.email import EmailStore


class InMemoryEmailStore(EmailStore):
    def __init__(self, store=None):
        """
        :type store: list[dict] | None

        """
        self._store = store or []

    def inbox(self, email_address):
        return (dict(email) for email in self._store
                if email_address in email.get('to', [])
                or email_address in email.get('cc', [])
                or email_address in email.get('bcc', []))

    def outbox(self, email_address):
        return (dict(email) for email in self._store
                if email_address == email.get('from')
                and email.get('sent_at') is None)

    def sent(self, email_address):
        return (dict(email) for email in self._store
                if email_address == email.get('from')
                and email.get('sent_at') is not None)

    def create(self, *emails):
        self._store.extend(map(dict, emails))

    def search(self, email_address, query):
        return (dict(email) for email in self._all_for(email_address)
                if query in email.get('subject', '')
                or query in email.get('body', '')
                or query in email.get('from', '')
                or any(query in to for to in email.get('to', []))
                or any(query in cc for cc in email.get('cc', []))
                or any(query in bcc for bcc in email.get('bcc', [])))

    def pending(self):
        return (dict(email) for email in self._store
                if email.get('sent_at') is None)

    def _all_for(self, email_address):
        return chain(self.inbox(email_address),
                     self.outbox(email_address),
                     self.sent(email_address))


class PersistentInMemoryEmailStore(InMemoryEmailStore):
    def __init__(self, store_location):
        """
        :type store_location: str

        """
        self._store_location = store_location
        store = self._load_store(store_location)
        super().__init__(store=store)
        atexit.register(self._dump_store)

    @classmethod
    def _load_store(cls, store_location):
        """
        :type store_location: str
        :rtype: list[dict]

        """
        try:
            with open(store_location) as fobj:
                return json.load(fobj)
        except (IOError, json.JSONDecodeError):
            return []

    def _dump_store(self):
        if not self._store:
            return

        with open(self._store_location, 'w') as fobj:
            json.dump(self._store, fobj, indent=2)
