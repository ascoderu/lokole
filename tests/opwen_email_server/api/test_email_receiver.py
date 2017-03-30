from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import email_receiver


class ReceiveTests(TestCase):
    @patch.object(email_receiver, 'QUEUE')
    @patch.object(email_receiver, 'STORAGE')
    def test_stores_and_processes_new_email(self, storage_mock, queue_mock):
        message, status = email_receiver.receive('some-mime-email')

        self.assertEqual(storage_mock.store_text.call_count, 1)
        self.assertEqual(queue_mock.enqueue.call_count, 1)
        self.assertEqual(status, 200)
