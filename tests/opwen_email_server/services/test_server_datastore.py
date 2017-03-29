from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.services import server_datastore


class StoreEmailTests(TestCase):
    @patch.object(server_datastore, 'STORAGE')
    @patch.object(server_datastore, 'INDEX')
    def test_stores_and_indexes_email(self, index_mock, storage_mock):
        server_datastore.store_email('c08ddf62-b27c-4de1-ab6f-474d75dc0bfd', {
            'to': ['foo@bar.com'],
            'from': 'baz@foo.com',
            'subject': 'Test email',
        })

        self.assertEqual(storage_mock.store_text.call_count, 1)
        self.assertEqual(index_mock.insert.call_count, 1)
