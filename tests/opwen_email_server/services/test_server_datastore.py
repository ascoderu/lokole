from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.services import server_datastore


class StoreEmailTests(TestCase):
    @patch.object(server_datastore, 'STORAGE')
    @patch.object(server_datastore, 'INDEX')
    def test_stores_and_indexes_email(self, index_mock, storage_mock):
        server_datastore.store_email('c08ddf62-b27c-4de1-ab6f-474d75dc0bfd', {
            'to': ['foo@bar.com'],
            'from': 'baz@foo.com',
            'subject': 'Test email',
        })

        self.assertEqual(storage_mock.store_text.call_count, 1)
        self.assertEqual(index_mock.insert.call_count, 1)


class FetchEmailTests(TestCase):
    @patch.object(server_datastore.STORAGE, 'fetch_text')
    def test_retrieves_email(self, fetch_mock):
        email_id = '124966bc-150b-11e7-93ae-92361f002671'
        email = {'to': ['test@foo.com']}
        fetch_mock.return_value = '{"to": ["test@foo.com"]}'

        actual = server_datastore.fetch_email(email_id)

        self.assertEqual(email, actual)
        fetch_mock.assert_called_once_with(email_id)


class MarkEmailsAsDeliveredTests(TestCase):
    @patch.object(server_datastore, 'INDEX')
    def test_deletes_emails(self, index_mock):
        server_datastore.mark_emails_as_delivered('foo.com', ['1', '2'])

        self.assertEqual(index_mock.delete.call_count, 1)


class FetchPendingEmailsTests(TestCase):
    @patch.object(server_datastore, 'fetch_email')
    @patch.object(server_datastore, 'INDEX')
    def test_deletes_emails(self, index_mock, fetch_mock):
        email_ids = ['1', '2', '3']
        index_mock.query.return_value = email_ids

        list(server_datastore.fetch_pending_emails('foo.com'))

        self.assertEqual(fetch_mock.call_count, len(email_ids))
