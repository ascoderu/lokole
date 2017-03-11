from unittest import TestCase
from unittest.mock import patch

from opwen_email_server.api import datastore


class StoreEmailTests(TestCase):
    @patch('opwen_email_server.api.datastore.BLOB_SERVICE')
    @patch('opwen_email_server.api.datastore.TABLE_SERVICE')
    def test_stores_and_indexes_email(self, table_mock, blob_mock):
        datastore.store_email('c08ddf62-b27c-4de1-ab6f-474d75dc0bfd', {
            'to': ['foo@bar.com'],
            'from': 'baz@foo.com',
            'subject': 'Test email',
        })

        self.assertEqual(blob_mock.create_blob_from_text.call_count, 1)
        self.assertEqual(table_mock.commit_batch.call_count, 5)
