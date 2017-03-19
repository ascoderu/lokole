from contextlib import contextmanager
from os import environ
from unittest import TestCase
from unittest.mock import patch


class UploadTests(TestCase):
    def test_schedules_upload_for_client(self):
        with self._given_clients('{"client1": "id1"}') as (upload, mock_queue):
            message, status = upload({'client_id': 'client1'})
            self.assertEqual(status, 200)
            self.assertEqual(mock_queue.enqueue.call_count, 1)

    def test_denies_unknown_client(self):
        with self._given_clients('{"client1": "id1"}') as (upload, _):
            message, status = upload({'client_id': 'unknown'})
            self.assertEqual(status, 403)

    @classmethod
    @contextmanager
    def _given_clients(cls, clients: str):
        environ['OPWEN_CLIENTS'] = clients
        from opwen_email_server.api import lokole_write
        with patch.object(lokole_write, 'QUEUE') as mock_queue:
            yield lokole_write.upload, mock_queue
        del lokole_write
