from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import sendgrid


class ReceiveTests(TestCase):
    @patch.object(sendgrid, 'QUEUE')
    @patch.object(sendgrid, 'STORAGE')
    def test_stores_and_processes_new_email(self, storage_mock, queue_mock):
        message, status = sendgrid.receive('some-mime-email')

        self.assertEqual(storage_mock.store_text.call_count, 1)
        self.assertEqual(queue_mock.enqueue.call_count, 1)
        self.assertEqual(status, 200)
