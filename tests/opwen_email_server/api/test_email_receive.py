from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import email_receive
from tests.opwen_email_server.api.api_test_base import AuthTestMixin


class ReceiveTests(TestCase, AuthTestMixin):
    @patch.object(email_receive, 'QUEUE')
    @patch.object(email_receive, 'STORAGE')
    def test_stores_and_processes_new_email(self, storage_mock, queue_mock):
        with self.given_clients(email_receive, {'client1': 'id1'}):
            message, status = email_receive.receive('client1', 'mime-email')

            self.assertEqual(storage_mock.store_text.call_count, 1)
            self.assertEqual(queue_mock.enqueue.call_count, 1)
            self.assertEqual(status, 200)

    def test_denies_unknown_client(self):
        with self.given_clients(email_receive, {'client1': 'id1'}):
            message, status = email_receive.receive('unknown', 'mime-email')
            self.assertEqual(status, 403)
