from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import client_write
from tests.opwen_email_server.api.api_test_base import AuthTestMixin


class UploadTests(TestCase, AuthTestMixin):
    @patch.object(client_write, 'tasks')
    def test_schedules_upload_for_client(self, mock_queue):
        with self.given_clients(client_write, {'client1': 'id1'}):
            message, status = client_write.upload('client1', {})
            self.assertEqual(status, 200)
            self.assertEqual(mock_queue.written_store.delay.call_count, 1)

    def test_denies_unknown_client(self):
        with self.given_clients(client_write, {'client1': 'id1'}):
            message, status = client_write.upload('unknown', {})
            self.assertEqual(status, 403)
