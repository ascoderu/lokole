from collections import namedtuple
from contextlib import contextmanager
from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import client_read
from opwen_email_server.services.auth import EnvironmentAuth


class DownloadTests(TestCase):
    def test_denies_unknown_client(self):
        self.given_requester('unknown')
        with self.given_clients({'client1': 'bar.com'}):
            message, status = client_read.download()
            self.assertEqual(status, 403)

    @patch.object(client_read, 'server_datastore')
    @patch.object(client_read, 'STORAGE')
    def test_uploads_emails_and_marks_as_delivered(
            self, storage_mock, datastore_mock):

        self.given_requester('client1')
        with self.given_clients({'client1': 'bar.com'}):
            resource_id = '1234'
            emails = [{'to': 'foo@bar.com', '_uid': '1'},
                       {'to': 'bar@bar.com', '_uid': '2'}]
            self.given_index(datastore_mock, storage_mock, emails, resource_id)

            response = client_read.download()

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

    @contextmanager
    def given_clients(self, clients):
        original_clients = client_read.CLIENTS
        client_read.CLIENTS = EnvironmentAuth(clients)
        yield
        client_read.CLIENTS = original_clients

    def given_requester(self, client):
        def restore_request():
            client_read.request = self._original_request
        request_type = namedtuple('Request', 'headers')
        request_mock = request_type({'X-LOKOLE-ClientId': client})
        self._original_request = client_read.request
        client_read.request = request_mock
        self.addCleanup(restore_request)
