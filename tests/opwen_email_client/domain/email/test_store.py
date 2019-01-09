from abc import ABCMeta
from abc import abstractmethod
from unittest import TestCase
from typing import Iterable
from typing import List

from opwen_email_client.domain.email.store import EmailStore


class Base(object):
    class EmailStoreTests(TestCase, metaclass=ABCMeta):
        @abstractmethod
        def create_email_store(self, restricted=None) -> EmailStore:
            raise NotImplementedError

        def setUp(self):
            self.email_store = self.create_email_store()

        def given_emails(self, *emails: dict) -> List[dict]:
            self.email_store.create(emails)
            return list(emails)

        def assertContainsEmail(self, expected: dict, collection: Iterable[dict]):
            def cleanup(email):
                email = {key: value for (key, value) in email.items() if value}
                email['from'] = email.get('from', '').lower() or None
                email['to'] = [_.lower() for _ in email.get('to', [])] or None
                email['cc'] = [_.lower() for _ in email.get('cc', [])] or None
                email['bcc'] = [_.lower() for _ in email.get('bcc', [])] or None
                return email

            self.assertIn(cleanup(expected), [cleanup(actual) for actual in collection])

        def test_creates_email_id(self):
            email = self.given_emails(
                {'to': ['foo@bar.com']})[0]

            self.assertIsNotNone(email.get('_uid'), 'email id was not set')

        def test_filters_restricted_inboxes(self):
            restricted1 = 'restricted@test.com'
            allowed1, allowed2 = 'allowed1@bar.com', 'allowed2@baz.com'

            self.email_store = self.create_email_store(
                {restricted1: {allowed1, allowed2}})

            kept = self.given_emails(
                {'to': [restricted1], 'from': allowed1},
                {'to': [restricted1], 'from': allowed1},
                {'cc': [restricted1], 'from': allowed2},
                {'bcc': [restricted1, allowed1], 'from': allowed2})
            self.given_emails(
                {'to': [restricted1], 'from': 'unknown1@baz.com'},
                {'cc': [restricted1], 'from': 'unknown2@baz.com'},
                {'cc': [restricted1], 'from': 'unknown2@baz.com'},
                {'bcc': [restricted1], 'from': 'unknown3@baz.com'})

            results = list(self.email_store.inbox(restricted1))
            self.assertEqual(len(results), 4)
            self.assertContainsEmail(kept[0], results)
            self.assertContainsEmail(kept[1], results)
            self.assertContainsEmail(kept[2], results)
            self.assertContainsEmail(kept[3], results)

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
                {'to': ['Foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'to': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'cc': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'bcc': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'})

            results = list(self.email_store.inbox('foo@bar.com'))

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[1], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_outbox(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'Foo@bar.com', 'sent_at': None},
                {'to': ['foo@bar.com']},
                {'cc': ['foo@bar.com']},
                {'bcc': ['foo@bar.com']},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'})

            results = list(self.email_store.outbox('foo@bar.com'))

            self.assertEqual(len(results), 3)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_pending(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'baz@bar.com'},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'})

            results = list(self.email_store.pending())

            self.assertEqual(len(results), 3)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_sent(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'to': ['foo@bar.com']},
                {'cc': ['foo@bar.com']},
                {'bcc': ['foo@bar.com']},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'})

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

        def test_delete(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'deleted1'},
                {'to': ['foo@bar.com'], 'subject': 'deleted2'},
                {'to': ['foo@bar.com'], 'subject': 'not-deleted1'},
                {'to': ['foo@bar.com'], 'subject': 'not-deleted2'},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            self.email_store.delete('foo@bar.com', emails[:2])
            deleted_emails = list(self.email_store.inbox('foo@bar.com'))
            unchanged_emails = list(self.email_store.inbox('baz@bar.com'))

            self.assertEqual(len(deleted_emails), 2)
            self.assertEqual(deleted_emails[0]['_uid'], emails[2]['_uid'])
            self.assertEqual(deleted_emails[1]['_uid'], emails[3]['_uid'])
            self.assertEqual(len(unchanged_emails), 1)
            self.assertEqual(unchanged_emails[0]['_uid'], emails[4]['_uid'])

        def test_get(self):
            given = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo',
                 'attachments': [{'filename': 'foo.txt',
                                  'content': b'foo.txt',
                                  'cid': None}]},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            actual = self.email_store.get(given[0]['_uid'])

            self.assertEqual(actual, given[0])

        def test_get_without_match(self):
            self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'})

            actual = self.email_store.get('uid-does-not-exist')

            self.assertIsNone(actual)
