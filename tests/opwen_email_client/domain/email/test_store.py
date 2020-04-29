from abc import ABCMeta
from abc import abstractmethod
from unittest import TestCase
from typing import Iterable
from typing import List

from opwen_email_client.domain.email.store import EmailStore


class Base(object):
    class EmailStoreTests(TestCase, metaclass=ABCMeta):
        page_size = 10

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
            email = self.given_emails({'to': ['foo@bar.com']})[0]

            self.assertIsNotNone(email.get('_uid'), 'email id was not set')

        def test_filters_restricted_inboxes(self):
            restricted1 = 'restricted@test.com'
            allowed1, allowed2 = 'allowed1@bar.com', 'allowed2@baz.com'

            self.email_store = self.create_email_store({restricted1: {allowed1, allowed2}})

            kept = self.given_emails(
                {'to': [restricted1], 'from': allowed1},
                {'to': [restricted1], 'from': allowed1},
                {'cc': [restricted1], 'from': allowed2},
                {'bcc': [restricted1, allowed1], 'from': allowed2},
            )
            self.given_emails(
                {'to': [restricted1], 'from': 'unknown1@baz.com'},
                {'cc': [restricted1], 'from': 'unknown2@baz.com'},
                {'cc': [restricted1], 'from': 'unknown2@baz.com'},
                {'bcc': [restricted1], 'from': 'unknown3@baz.com'},
            )

            results = self.email_store.inbox(restricted1, page=1)
            results = list(results)

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(kept[0], results)
            self.assertContainsEmail(kept[1], results)
            self.assertContainsEmail(kept[2], results)
            self.assertContainsEmail(kept[3], results)

        def test_does_not_overwrite_email_id(self):
            emails1 = self.given_emails(
                {'to': ['foo@bar.com']},
                {'to': ['foo@bar.com']},
            )
            emails2 = self.given_emails(
                {'to': ['bar@bar.com']},
                *emails1,
            )

            results = self.email_store.inbox('foo@bar.com', page=1)
            self.assertEqual(len(list(results)), 2)

            results = self.email_store.inbox('bar@bar.com', page=1)
            self.assertEqual(len(list(results)), 1)

            ids1 = [_['_uid'] for _ in emails1]
            ids2 = [_['_uid'] for _ in emails2[1:]]
            self.assertEqual(ids1, ids2)

        def test_create_with_existing_attachment(self):
            self.given_emails({
                'to': ['foo@bar.com'], 'attachments': [
                    {'_uid': 'a1', 'filename': 'a1', 'content': b'a1'},
                    {'_uid': 'a2', 'filename': 'a2', 'content': b'a2'},
                ]
            })

            self.given_emails({
                'to': ['foo@bar.com'], 'attachments': [
                    {'_uid': 'a1', 'filename': 'a1', 'content': b'a1'},
                    {'_uid': 'a3', 'filename': 'a3', 'content': b'a3'},
                ]
            })

            results = self.email_store.inbox('foo@bar.com', page=1)
            self.assertEqual(len(list(results)), 2)

        def test_inbox(self):
            emails = self.given_emails(
                {'to': ['Foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'to': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'cc': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'bcc': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'},
            )

            results = self.email_store.inbox('foo@bar.com', page=1)
            results = list(results)

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[1], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_inbox_paginated(self):
            self.given_emails(*[{
                'to': ['Foo@bar.com'],
                'subject': 'email{}'.format(i),
                'sent_at': '2017-09-10 11:11',
            } for i in range(self.page_size + 3)])

            results = self.email_store.inbox('foo@bar.com', page=1)
            results = list(results)
            self.assertEqual(len(results), self.page_size)

            results = self.email_store.inbox('foo@bar.com', page=2)
            results = list(results)
            self.assertEqual(len(results), 3)

        def test_unread(self):
            self.given_emails(
                {'to': ['Foo@bar.com'], 'sent_at': '2017-09-10 11:11', 'read': False},
                {'to': ['foo@bar.com'], 'sent_at': '2017-09-10 11:11', 'read': True},
                {'to': ['bar@bar.com'], 'sent_at': '2017-09-10 11:11', 'read': True},
                {'to': ['baz@bar.com'], 'sent_at': '2017-09-10 11:11'},
            )

            result = self.email_store.has_unread('foo@bar.com')

            self.assertTrue(result)

            result = self.email_store.has_unread('bar@bar.com')

            self.assertFalse(result)

            result = self.email_store.has_unread('baz@bar.com')

            self.assertTrue(result)

        def test_outbox(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'Foo@bar.com', 'sent_at': None},
                {'to': ['foo@bar.com']},
                {'cc': ['foo@bar.com']},
                {'bcc': ['foo@bar.com']},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'},
            )

            results = self.email_store.outbox('foo@bar.com', page=1)
            results = list(results)

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
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'},
            )

            results = self.email_store.pending(page=1)
            results = list(results)

            self.assertEqual(len(results), 3)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)

        def test_pending_without_pagination(self):
            self.given_emails(*[{
                'from': 'foo@bar.com',
                'subject': 'email{}'.format(i),
                'sent_at': None,
            } for i in range(self.page_size + 3)])

            results = self.email_store.pending(page=None)
            results = list(results)

            self.assertEqual(len(results), 13)

        def test_num_pending(self):
            count = self.email_store.num_pending()

            self.assertEqual(count, 0)

            self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'from': 'baz@bar.com'},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'},
            )

            count = self.email_store.num_pending()

            self.assertEqual(count, 3)

        def test_sent(self):
            emails = self.given_emails(
                {'from': 'foo@bar.com'},
                {'from': 'foo@bar.com', 'sent_at': '2017-09-10 11:11'},
                {'from': 'foo@bar.com', 'sent_at': None},
                {'to': ['foo@bar.com']},
                {'cc': ['foo@bar.com']},
                {'bcc': ['foo@bar.com']},
                {'from': 'baz@bar.com', 'sent_at': '2017-09-10 11:11'},
            )

            results = self.email_store.sent('foo@bar.com', page=1)
            results = list(results)

            self.assertEqual(len(results), 1)
            self.assertContainsEmail(emails[1], results)

        def test_search_for_sender(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'from': 'baz@bar.com'},
                {'to': ['foo@bar.com'], 'from': 'fuz@bar.com'},
                {'to': ['baz@bar.com'], 'from': 'fuz@bar.com'},
            )

            results = self.email_store.search('foo@bar.com', page=1, query='fuz')
            results = list(results)

            self.assertEqual(len(results), 1)
            self.assertContainsEmail(emails[1], results)

        def test_search_for_body(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'body': 'bar koala bar'},
                {'to': ['foo@bar.com'], 'body': 'baz'},
                {'from': 'foo@bar.com', 'body': 'koala'},
                {'cc': ['foo@bar.com'], 'body': 'koala'},
                {'bcc': ['foo@bar.com'], 'body': 'koala'},
                {'to': ['baz@bar.com'], 'body': 'baz'},
            )

            results = self.email_store.search('foo@bar.com', page=1, query='koala')
            results = list(results)

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
                {'to': ['baz@bar.com'], 'subject': 'baz'},
            )

            results = self.email_store.search('foo@bar.com', page=1, query='koala')
            results = list(results)

            self.assertEqual(len(results), 4)
            self.assertContainsEmail(emails[0], results)
            self.assertContainsEmail(emails[2], results)
            self.assertContainsEmail(emails[3], results)
            self.assertContainsEmail(emails[4], results)

        def test_search_without_query(self):
            self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'bar foo bar'},
                {'to': ['baz@bar.com'], 'subject': 'baz'},
            )

            results = self.email_store.search('foo@bar.com', page=1, query=None)
            results = list(results)

            self.assertEqual(results, [])

        def test_mark_sent(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'},
            )

            self.email_store.mark_sent(emails)

            pending = self.email_store.pending(page=1)
            pending = list(pending)

            self.assertEqual(pending, [])

        def test_mark_read(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'},
            )

            self.email_store.mark_read('foo@bar.com', emails)

            read_emails = self.email_store.inbox('foo@bar.com', page=1)
            read_emails = list(read_emails)

            unchanged_emails = self.email_store.inbox('baz@bar.com', page=1)
            unchanged_emails = list(unchanged_emails)

            self.assertTrue(all(email.get('read') for email in read_emails))
            self.assertTrue(not any(email.get('read') for email in unchanged_emails))

        def test_delete(self):
            emails = self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'deleted1'},
                {'to': ['foo@bar.com'], 'subject': 'deleted2'},
                {'to': ['foo@bar.com'], 'subject': 'not-deleted1'},
                {'to': ['foo@bar.com'], 'subject': 'not-deleted2'},
                {'to': ['baz@bar.com'], 'subject': 'bar'},
            )

            self.email_store.delete('foo@bar.com', emails[:2])

            deleted_emails = self.email_store.inbox('foo@bar.com', page=1)
            deleted_emails = list(deleted_emails)

            unchanged_emails = self.email_store.inbox('baz@bar.com', page=1)
            unchanged_emails = list(unchanged_emails)

            self.assertEqual(len(deleted_emails), 2)
            self.assertEqual(deleted_emails[0]['_uid'], emails[2]['_uid'])
            self.assertEqual(deleted_emails[1]['_uid'], emails[3]['_uid'])
            self.assertEqual(len(unchanged_emails), 1)
            self.assertEqual(unchanged_emails[0]['_uid'], emails[4]['_uid'])

        def test_get(self):
            given = self.given_emails(
                {
                    'to': ['foo@bar.com'], 'subject': 'foo', 'attachments':
                    [{'filename': 'foo.txt', 'content': b'foo.txt', 'cid': None}]
                },
                {'to': ['baz@bar.com'], 'subject': 'bar'},
            )

            actual = self.email_store.get(given[0]['_uid'])

            self.assertEqual(actual, given[0])

        def test_get_with_separate_attachments(self):
            self.given_emails(
                {'_type': 'email', '_uid': 'e1', 'to': ['foo@bar.com'], 'subject': 'foo'},
                {'_type': 'email', '_uid': 'e2', 'to': ['baz@bar.com'], 'subject': 'bar'},
                {'_type': 'email', '_uid': 'e3', 'to': ['buz@buz.com'], 'subject': 'buz'},
                {'_type': 'email', '_uid': 'e4', 'to': ['buz@foo.com'], 'subject': 'foobuz'},
                {
                    '_type': 'attachment', '_uid': 'a1', 'emails': ['e1', 'e4'], 'filename': 'foo.txt', 'content':
                    b'foo.txt', 'cid': None
                },
                {
                    '_type': 'attachment', '_uid': 'a2', 'emails': ['e3'], 'filename': 'bar.txt', 'content': b'bar.txt',
                    'cid': None
                },
            )

            actual1 = self.email_store.get('e1')
            actual4 = self.email_store.get('e4')

            self.assertEqual(actual1.get('attachments'),
                             [{'_uid': 'a1', 'filename': 'foo.txt', 'content': b'foo.txt', 'cid': None}])

            self.assertEqual(actual1.get('attachments'), actual4.get('attachments'))

            actual3 = self.email_store.get('e3')

            self.assertEqual(actual3.get('attachments'),
                             [{'_uid': 'a2', 'filename': 'bar.txt', 'content': b'bar.txt', 'cid': None}])

            actual2 = self.email_store.get('e2')

            self.assertIsNone(actual2.get('attachments'))

        def test_get_without_match(self):
            self.given_emails(
                {'to': ['foo@bar.com'], 'subject': 'foo'},
                {'to': ['baz@bar.com'], 'subject': 'bar'},
            )

            actual = self.email_store.get('uid-does-not-exist')

            self.assertIsNone(actual)

        def test_get_attachment(self):
            self.given_emails(
                {
                    '_type': 'attachment', '_uid': 'a1', 'emails': ['e1', 'e4'], 'filename': 'foo.txt', 'content':
                    b'foo.txt', 'cid': None
                },
                {
                    '_type': 'attachment', '_uid': 'a2', 'emails': ['e3'], 'filename': 'bar.txt', 'content': b'bar.txt',
                    'cid': None
                },
            )

            actual = self.email_store.get_attachment('e1', 'a1')
            self.assertEqual(actual['_uid'], 'a1')

            actual = self.email_store.get_attachment('e3', 'a2')
            self.assertEqual(actual['_uid'], 'a2')

        def test_get_attachment_without_match(self):
            self.given_emails(
                {
                    '_type': 'attachment', '_uid': 'a1', 'emails': ['e1', 'e4'], 'filename': 'foo.txt', 'content':
                    b'foo.txt', 'cid': None
                },
                {
                    '_type': 'attachment', '_uid': 'a2', 'emails': ['e3'], 'filename': 'bar.txt', 'content': b'bar.txt',
                    'cid': None
                },
            )

            actual = self.email_store.get_attachment('email-does-not-exist', 'uid-does-not-exist')

            self.assertIsNone(actual)
