from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.backend import server_datastore
from opwen_email_server.api import store_inbound_emails


class StoreInboundEmailsTests(TestCase):
    @patch.object(store_inbound_emails, 'STORAGE')
    @patch.object(server_datastore, 'store_inbound_email')
    @patch.object(store_inbound_emails, 'parse_mime_email')
    def test_reads_message_and_stores_email(
            self, parser_mock, store_mock, storage_mock):

        email_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email = {'to': ['foo@bar.com']}
        parser_mock.return_value = email

        store_inbound_emails.store(email_id)

        self.assertEqual(storage_mock.fetch_text.call_count, 1)
        self.assertEqual(storage_mock.delete.call_count, 1)
        store_mock.assert_called_once_with(email_id, email)
