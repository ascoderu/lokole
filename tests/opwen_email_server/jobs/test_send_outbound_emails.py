from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.jobs import send_outbound_emails


class SendOutboundEmailsTests(TestCase):
    @patch.object(email_sender, 'QUEUE')
    @patch.object(server_datastore, 'fetch_email')
    @patch.object(email_sender, 'send')
    def test_reads_message_and_stores_email(
            self, send_mock, fetch_mock, queue_mock):

        email_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email = {'to': ['foo@bar.com'], '_uid': email_id}
        self._given_message(email, email_id, fetch_mock, queue_mock)
        consumer = send_outbound_emails.Job()

        consumer._run_once()

        self.assertEqual(queue_mock.dequeue.call_count, 1)
        fetch_mock.assert_called_once_with(email_id)
        send_mock.assert_called_once_with(email)

    @classmethod
    def _given_message(cls, email, email_id, fetch_mock, queue_mock):
        queue_mock.dequeue.return_value = [{'resource_id': email_id}]
        fetch_mock.return_value = email
