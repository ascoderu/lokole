from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import sendgrid


class ReceiveTests(TestCase):
    @patch('opwen_email_server.api.sendgrid.QUEUE_SERVICE')
    @patch('opwen_email_server.api.sendgrid.BLOB_SERVICE')
    def test_stores_and_processes_incoming_email(self, blob_mock, queue_mock):
        sendgrid.receive('some-mime-email')

        self.assertEqual(blob_mock.create_blob_from_text.call_count, 1)
        self.assertEqual(queue_mock.put_message.call_count, 1)
