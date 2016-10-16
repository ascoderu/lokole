from abc import ABCMeta
from abc import abstractmethod
from os import remove
from tempfile import NamedTemporaryFile
from unittest import TestCase

from ca.ascoderu.lokole.domain.email.base64 import Base64AttachmentEncoder
from ca.ascoderu.lokole.domain.email.memory import InMemoryEmailStore
from ca.ascoderu.lokole.domain.email.memory import PersistentInMemoryEmailStore


class Base(object):
    class AttachmentEncoderTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_encoder(self):
            """
            :rtype: ca.ascoderu.lokole.domain.email.AttachmentEncoder

            """
            raise NotImplementedError

        @property
        def encodable_objects(self):
            """
            :rtype: collections.Iterable

            """
            yield b'some bytes'
            yield u'some unicode bytes: \u2603'.encode('utf-8')

        def setUp(self):
            self.encoder = self.create_encoder()

        def test_encoding_roundtrip(self):
            for original in self.encodable_objects:
                encoded = self.encoder.encode(original)
                decoded = self.encoder.decode(encoded)
                self.assertEqual(original, decoded)

    class EmailStoreTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_email_store(self):
            """
            :rtype: ca.ascoderu.lokole.domain.email.EmailStore

            """
            raise NotImplementedError

        def setUp(self):
            self.email_store = self.create_email_store()

        def given_emails(self, *emails):
            """
            :type emails: list[dict]
            :rtype: list[dict]

            """
            for email in emails:
                self.email_store.create(email)
            return emails

        def test_inbox(self):
            emails = self.given_emails(
                {'to': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'cc': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'bcc': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.inbox('foo@bar.com'))

            self.assertEqual(len(results), 3)
            self.assertIn(emails[0], results)
            self.assertIn(emails[1], results)
            self.assertIn(emails[2], results)

        def test_outbox(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'to': 'foo@bar.com'},
                {'cc': 'foo@bar.com'},
                {'bcc': 'foo@bar.com'},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.outbox('foo@bar.com'))

            self.assertEqual(len(results), 2)
            self.assertIn(emails[0], results)
            self.assertIn(emails[2], results)

        def test_pending(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'baz@bar.com'},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.pending())

            self.assertEqual(len(results), 3)
            self.assertIn(emails[0], results)
            self.assertIn(emails[2], results)
            self.assertIn(emails[3], results)

        def test_sent(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'to': 'foo@bar.com'},
                {'cc': 'foo@bar.com'},
                {'bcc': 'foo@bar.com'},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.sent('foo@bar.com'))

            self.assertEqual(len(results), 1)
            self.assertIn(emails[1], results)

        def test_search(self):
            emails = self.given_emails(
                {'to': 'foo@bar.com', 'subject': 'bar foo bar'},
                {'to': 'foo@bar.com', 'subject': 'baz'},
                {'from': 'foo@bar.com', 'subject': 'foo'},
                {'cc': 'foo@bar.com', 'subject': 'foo'},
                {'bcc': 'foo@bar.com', 'subject': 'foo'},
                {'to': 'baz@bar.com', 'subject': 'baz'})

            results = list(self.email_store.search('foo@bar.com', query='foo'))

            self.assertEqual(len(results), 4)
            self.assertIn(emails[0], results)
            self.assertIn(emails[2], results)
            self.assertIn(emails[3], results)
            self.assertIn(emails[4], results)

        def test_search_without_query(self):
            self.given_emails(
                {'to': 'foo@bar.com', 'subject': 'bar foo bar'},
                {'to': 'baz@bar.com', 'subject': 'baz'})

            results = list(self.email_store.search('foo@bar.com', query=None))

            self.assertEqual(results, [])


class Base64AttachmentEncoderTests(Base.AttachmentEncoderTests):
    def create_encoder(self):
        return Base64AttachmentEncoder()


class InMemoryEmailStoreTests(Base.EmailStoreTests):
    def create_email_store(self):
        return InMemoryEmailStore()


class PersistentInMemoryEmailStoreTests(Base.EmailStoreTests):
    def create_email_store(self):
        with NamedTemporaryFile(delete=False) as fobj:
            self._store_location = fobj.name
        return PersistentInMemoryEmailStore(self._store_location)

    def tearDown(self):
        remove(self._store_location)

    # noinspection PyUnresolvedReferences
    def test_persistence(self):
        emails = self.given_emails({'to': 'foo@bar.com'})

        self.email_store._dump_store()
        reloaded = PersistentInMemoryEmailStore(self._store_location)._store

        self.assertEqual(len(reloaded), 1)
        self.assertIn(emails[0], reloaded)

    # noinspection PyUnresolvedReferences
    def test_persistence_without_content(self):
        self.given_emails()

        self.email_store._dump_store()
        reloaded = PersistentInMemoryEmailStore(self._store_location)._store

        self.assertEqual(reloaded, [])
