from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.backend import server_datastore
from opwen_email_server.api import store_written_client_emails


class StoreWrittenClientEmailsTests(TestCase):
    @patch.object(store_written_client_emails, 'tasks')
    @patch.object(store_written_client_emails, 'STORAGE')
    @patch.object(server_datastore, 'store_outbound_email')
    def test_reads_message_and_stores_email(
            self, store_mock, client_storage_mock, send_queue_mock):

        resource_id = '7ad33d8a-c1ee-44c7-a655-fb0d167dc380'
        email1_id = '4efba428-143c-11e7-93ae-92361f002671'
        email2_id = 'c91636ee-143f-11e7-93ae-92361f002671'
        email1 = {'to': ['foo@test.com'], '_uid': email1_id}
        email2 = {'to': ['bar@test.com'], '_uid': email2_id}
        client_storage_mock.fetch_objects.return_value = [email1, email2]

        store_written_client_emails.store(resource_id)

        self.assertEqual(client_storage_mock.fetch_objects.call_count, 1)
        self.assertEqual(client_storage_mock.delete.call_count, 1)
        self.assertEqual(send_queue_mock.send.delay.call_count, 2)
        self.assertEqual(store_mock.call_count, 2)
        store_mock.assert_any_call(email1_id, email1)
        store_mock.assert_any_call(email2_id, email2)
