from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.backend import client_datastore
from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.api import store_written_client_emails


class StoreWrittenClientEmailsTests(TestCase):
    @patch.object(email_sender, 'QUEUE')
    @patch.object(client_datastore, 'unpack_emails')
    @patch.object(client_datastore, 'delete')
    @patch.object(server_datastore, 'store_email')
    def test_reads_message_and_stores_email(
            self, store_mock, delete_mock, unpack_mock, send_queue_mock):

        resource_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email1_id = '4efba428-143c-11e7-93ae-92361f002671'
        email2_id = 'c91636ee-143f-11e7-93ae-92361f002671'
        email1 = {'to': ['foo@test.com'], '_uid': email1_id}
        email2 = {'to': ['bar@test.com'], '_uid': email2_id}
        unpack_mock.return_value = [email1, email2]

        store_written_client_emails.store(resource_id)

        self.assertEqual(unpack_mock.call_count, 1)
        self.assertEqual(delete_mock.call_count, 1)
        self.assertEqual(send_queue_mock.enqueue.call_count, 2)
        self.assertEqual(store_mock.call_count, 2)
        store_mock.assert_any_call(email1_id, email1)
        store_mock.assert_any_call(email2_id, email2)
