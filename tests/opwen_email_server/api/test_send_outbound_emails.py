from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.api import send_outbound_emails


class SendOutboundEmailsTests(TestCase):
    @patch.object(server_datastore, 'fetch_email')
    @patch.object(email_sender, 'send')
    def test_reads_message_and_stores_email(self, send_mock, fetch_mock):
        email_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email = {'to': ['foo@bar.com'], '_uid': email_id}
        fetch_mock.return_value = email

        send_outbound_emails.send(email_id)

        fetch_mock.assert_called_once_with(email_id)
        send_mock.assert_called_once_with(email)
