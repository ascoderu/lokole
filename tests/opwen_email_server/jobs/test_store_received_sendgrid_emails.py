from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.jobs import store_received_sendgrid_emails


class StoreReceivedSendgridEmailsTests(TestCase):
    @patch.object(store_received_sendgrid_emails.sendgrid_receiver, 'QUEUE')
    @patch.object(store_received_sendgrid_emails.sendgrid_receiver, 'STORAGE')
    @patch.object(store_received_sendgrid_emails.server_datastore, 'store_email')
    @patch.object(store_received_sendgrid_emails, 'parse_mime_email')
    def test_reads_message_and_stores_email(
            self, parser_mock, store_mock, storage_mock, queue_mock):

        email_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email = {'to': ['foo@bar.com']}
        self._given_message(email, email_id, parser_mock, queue_mock)
        consumer = store_received_sendgrid_emails.SendgridQueueConsumer()

        consumer._run_once()

        self.assertEqual(storage_mock.fetch_text.call_count, 1)
        self.assertEqual(queue_mock.dequeue.call_count, 1)
        store_mock.assert_called_once_with(email_id, email)

    @classmethod
    def _given_message(cls, email, email_id, parser_mock, queue_mock):
        queue_mock.dequeue.return_value = [{'resource_id': email_id}]
        parser_mock.return_value = email
