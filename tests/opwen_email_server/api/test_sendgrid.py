from unittest import TestCase
from unittest.mock import Mock

from opwen_email_server.api import sendgrid


class ReceiveTests(TestCase):
    def setUp(self):
        self.blob_original = sendgrid.BLOB_SERVICE
        self.queue_original = sendgrid.QUEUE_SERVICE
        sendgrid.BLOB_SERVICE = self.blob_mock = Mock()
        sendgrid.QUEUE_SERVICE = self.queue_mock = Mock()

    def tearDown(self):
        sendgrid.BLOB_SERVICE = self.blob_original
        sendgrid.QUEUE_SERVICE = self.queue_original

    def test_stores_and_processes_incoming_email(self):
        sendgrid.receive('some-mime-email')

        self.assertEqual(self.blob_mock.create_blob_from_text.call_count, 1)
        self.assertEqual(self.queue_mock.put_message.call_count, 1)
