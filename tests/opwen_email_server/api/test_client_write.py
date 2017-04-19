from collections import namedtuple
from contextlib import contextmanager
from os import environ
from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import client_write


class UploadTests(TestCase):
    def test_schedules_upload_for_client(self):
        self.given_requester('client1')
        with self.given_clients('{"client1": "id1"}') as (upload, mock_queue):
            message, status = upload({})
            self.assertEqual(status, 200)
            self.assertEqual(mock_queue.enqueue.call_count, 1)

    def test_denies_unknown_client(self):
        self.given_requester('unknown')
        with self.given_clients('{"client1": "id1"}') as (upload, _):
            message, status = upload({})
            self.assertEqual(status, 403)

    def given_requester(self, client):
        def restore_request():
            client_write.request = self._original_request
        request_type = namedtuple('Request', 'headers')
        request_mock = request_type({'X-LOKOLE-ClientId': client})
        self._original_request = client_write.request
        client_write.request = request_mock
        self.addCleanup(restore_request)

    @classmethod
    @contextmanager
    def given_clients(cls, clients: str):
        environ['LOKOLE_CLIENTS'] = clients
        from opwen_email_server.api import client_write
        with patch.object(client_write, 'QUEUE') as mock_queue:
            yield client_write.upload, mock_queue
        del client_write
