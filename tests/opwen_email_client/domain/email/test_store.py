from abc import ABCMeta
from abc import abstractmethod
from os import remove
from tempfile import NamedTemporaryFile
from unittest import TestCase

from opwen_email_client.domain.email.store import SqliteEmailStore


class Base(object):
    class EmailStoreTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_email_store(self):
            """
            :rtype: opwen_domain.email.EmailStore

            """
            raise NotImplementedError

        def setUp(self):
            self.email_store = self.create_email_store()

        def given_emails(self, *emails):
            """
            :type emails: list[dict]
            :rtype: list[dict]

            """
            self.email_store.create(emails)
            return emails

        def assertContainsEmail(self, expected, collection):
            """
            :type expected: dict
            :type collection: collections.Iterable[dict]

            """
            def cleanup(email):
                return {key: value for (key, value) in email.items() if value}

            self.assertIn(cleanup(expected), [cleanup(actual) for actual in collection])

        def test_creates_email_id(self):
            email = self.given_emails(
                {'to': ['foo@bar.com']})[0]

            self.assertIsNotNone(email.get('_uid'), 'email id was not set')

        def test_does_not_overwrite_email_id(self):
            emails1 = self.given_emails(
                {'to': ['foo@bar.com']},
                {'to': ['foo@bar.com']})
            emails2 = self.given_emails(
                {'to': ['bar@bar.com']},
                *emails1)

            self.assertEqual(len(list(self.email_store.inbox('foo@bar.com'))), 2)
            self.assertEqual(len(list(self.email_store.inbox('bar@bar.com'))), 1)

            ids1 = [_['_uid'] for _ in emails1]
            ids2 = [_['_uid'] for _ in emails2[1:]]
            self.assertEqual(ids1, ids2)

        def test_inbox(self):
            emails = self.given_emails(
                {'to': ['Foo@bar.com'], 'sent_at': 'YYYY'},
                {'to': ['foo@bar.com'], 'sent_at': 'YYYY'},
                {'cc': ['foo@bar.com'], 'sent_at': 'YYYY'},
                {'bcc': ['foo@bar.com'], 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.inbox('foo@bar.com'))

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[1], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_outbox(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'Foo@bar.com', 'sent_at': None},
                {'to': ['foo@bar.com']},
                {'cc': ['foo@bar.com']},
                {'bcc': ['foo@bar.com']},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.outbox('foo@bar.com'))

            self.assertEqual(len(results), 3)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_pending(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'baz@bar.com'},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.pending())

            self.assertEqual(len(results), 3)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_sent(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': 'YYYY'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'to': ['foo@bar.com']},
                {'cc': ['foo@bar.com']},
                {'bcc': ['foo@bar.com']},
                {'from': 'baz@bar.com', 'sent_at': 'YYYY'})

            results = list(self.email_store.sent('foo@bar.com'))

            self.assertEqual(len(results), 1)
            self.assertContainsEmail(emails[1], results)

        def test_search_for_sender(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'from': 'baz@bar.com'},
                {'to': ['foo@bar.com'], 'from': 'fuz@bar.com'},
                {'to': ['baz@bar.com'], 'from': 'fuz@bar.com'})

            results = list(self.email_store.search('foo@bar.com', query='fuz'))

            self.assertEqual(len(results), 1)
            self.assertContainsEmail(emails[1], results)

        def test_search_for_body(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'body': 'bar koala bar'},
                {'to': ['foo@bar.com'], 'body': 'baz'},
                {'from': 'foo@bar.com', 'body': 'koala'},
                {'cc': ['foo@bar.com'], 'body': 'koala'},
                {'bcc': ['foo@bar.com'], 'body': 'koala'},
                {'to': ['baz@bar.com'], 'body': 'baz'})

            results = list(self.email_store.search('foo@bar.com', query='koala'))

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)
            self.assertContainsEmail(emails[4], results)

        def test_search_for_subject(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'bar koala bar'},
                {'to': ['foo@bar.com'], 'subject': 'baz'},
                {'from': 'foo@bar.com', 'subject': 'koala'},
                {'cc': ['foo@bar.com'], 'subject': 'koala'},
                {'bcc': ['foo@bar.com'], 'subject': 'koala'},
                {'to': ['baz@bar.com'], 'subject': 'baz'})

            results = list(self.email_store.search('foo@bar.com', query='koala'))

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)
            self.assertContainsEmail(emails[4], results)

        def test_search_without_query(self):
            self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'bar foo bar'},
                {'to': ['baz@bar.com'], 'subject': 'baz'})

            results = list(self.email_store.search('foo@bar.com', query=None))

            self.assertEqual(results, [])

        def test_mark_sent(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            self.email_store.mark_sent(emails)
            pending = list(self.email_store.pending())

            self.assertEqual(pending, [])

        def test_mark_read(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            self.email_store.mark_read('foo@bar.com', emails)
            read_emails = list(self.email_store.inbox('foo@bar.com'))
            unchanged_emails = list(self.email_store.inbox('baz@bar.com'))

            self.assertTrue(all(email.get('read') for email in read_emails))
            self.assertTrue(not any(email.get('read') for email in unchanged_emails))

        def test_get(self):
            given = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo',
                 'attachments': [{'filename': 'foo.txt', 'content': 'Zm9vLnR4dA=='}]},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            actual = self.email_store.get(given[0]['_uid'])

            self.assertEqual(actual, given[0])

        def test_get_without_match(self):
            self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            actual = self.email_store.get('uid-does-not-exist')

            self.assertIsNone(actual)


class SqliteEmailStoreTests(Base.EmailStoreTests):
    def create_email_store(self):
        return SqliteEmailStore(self.store_location, JsonSerializer())

    @classmethod
    def setUpClass(cls):
        with NamedTemporaryFile(delete=False) as fobj:
            cls.store_location = fobj.queue_name

    @classmethod
    def tearDownClass(cls):
        # noinspection PyUnresolvedReferences
        remove(cls.store_location)

    def tearDown(self):
        # noinspection PyUnresolvedReferences
        dbwrite = self.email_store._dbwrite
        # noinspection PyUnresolvedReferences
        base = self.email_store._base

        with dbwrite() as db:
            for table in reversed(base.metadata.sorted_tables):
                db.execute(table.delete())
