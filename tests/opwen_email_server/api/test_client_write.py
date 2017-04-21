from contextlib import contextmanager
from os import environ
from unittest import TestCase
from unittest.mock import patch


class UploadTests(TestCase):
    def test_schedules_upload_for_client(self):
        with self.given_clients('{"client1": "id1"}') as (upload, mock_queue):
            message, status = upload('client1', {})
            self.assertEqual(status, 200)
            self.assertEqual(mock_queue.enqueue.call_count, 1)

    def test_denies_unknown_client(self):
        with self.given_clients('{"client1": "id1"}') as (upload, _):
            message, status = upload('unknown', {})
            self.assertEqual(status, 403)

    @classmethod
    @contextmanager
    def given_clients(cls, clients: str):
        environ['LOKOLE_CLIENTS'] = clients
        from opwen_email_server.api import client_write
        with patch.object(client_write, 'QUEUE') as mock_queue:
            yield client_write.upload, mock_queue
        del client_write
