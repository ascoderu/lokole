from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import client_read
from tests.opwen_email_server.api.api_test_base import AuthTestMixin


class DownloadTests(TestCase, AuthTestMixin):
    def test_denies_unknown_client(self):
        with self.given_clients(client_read, {'client1': 'bar.com'}):
            message, status = client_read.download('unknown')
            self.assertEqual(status, 403)

    @patch.object(client_read, 'server_datastore')
    @patch.object(client_read, 'STORAGE')
    def test_uploads_emails_and_marks_as_delivered(
            self, storage_mock, datastore_mock):

        with self.given_clients(client_read, {'client1': 'bar.com'}):
            resource_id = '1234'
            emails = [{'to': 'foo@bar.com', '_uid': '1'},
                       {'to': 'bar@bar.com', '_uid': '2'}]
            self.given_index(datastore_mock, storage_mock, emails, resource_id)

            response = client_read.download('client1')

            self.assertEqual(resource_id, response.get('resource_id'))
            self.assertEqual(self.stored_ids, emails)
            datastore_mock.mark_emails_as_delivered.\
                assert_called_once_with('bar.com', {'1', '2'})

    def given_index(self, datastore_mock, storage_mock, emails, resource):
        def store_objects(objs):
            self.stored_ids = list(objs)
            return resource
        self.stored_ids = []
        datastore_mock.fetch_pending_emails.return_value = emails
        storage_mock.store_objects.side_effect = store_objects
