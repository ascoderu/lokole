from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import email_receive


class ReceiveTests(TestCase):
    @patch.object(email_receive, 'QUEUE')
    @patch.object(email_receive, 'STORAGE')
    def test_stores_and_processes_new_email(self, storage_mock, queue_mock):
        message, status = email_receive.receive('some-mime-email')

        self.assertEqual(storage_mock.store_text.call_count, 1)
        self.assertEqual(queue_mock.enqueue.call_count, 1)
        self.assertEqual(status, 200)
