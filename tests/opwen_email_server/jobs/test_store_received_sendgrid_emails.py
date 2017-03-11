from collections import namedtuple
from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.jobs import store_received_sendgrid_emails


_MESSAGE = namedtuple('Message', 'content id pop_receipt')


class StoreReceivedSendgridEmailsTests(TestCase):
    @patch('opwen_email_server.api.sendgrid.QUEUE_SERVICE')
    @patch('opwen_email_server.api.sendgrid.BLOB_SERVICE')
    @patch('opwen_email_server.api.datastore.store_email')
    @patch.object(store_received_sendgrid_emails, 'parse_mime_email')
    def test_reads_message_and_stores_email(
            self, parser_mock, store_mock, blob_mock, queue_mock):

        email_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email = {'to': ['foo@bar.com']}
        self._given_message(email, email_id, parser_mock, queue_mock)

        store_received_sendgrid_emails.run_once()

        self.assertEqual(blob_mock.get_blob_to_text.call_count, 1)
        self.assertEqual(queue_mock.get_messages.call_count, 1)
        self.assertEqual(queue_mock.delete_message.call_count, 1)
        store_mock.assert_called_once_with(email_id, email)

    @classmethod
    def _given_message(cls, email, email_id, parser_mock, queue_mock):
        queue_mock.get_messages.return_value = [
            _MESSAGE('{"blob_name":"%s"}' % email_id, 'id', 'ack'),
        ]
        parser_mock.return_value = email
