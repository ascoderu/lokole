from collections import namedtuple
from unittest import TestCase
from unittest.mock import MagicMock

from opwen_email_server.services.storage import AzureStorage


class AzureStorageTests(TestCase):
    def test_creates_container_only_once(self):
        expected_content = 'some content'
        storage, client_mock = self._given_storage(expected_content)

        storage.fetch_text('id1')
        storage.fetch_text('id1')

        self.assertEqual(client_mock.create_container.call_count, 1)

    def test_fetches_text(self):
        expected_content = 'some content'
        storage, client_mock = self._given_storage(expected_content)

        content = storage.fetch_text('id1')

        self.assertEqual(client_mock.get_blob_to_text.call_count, 1)
        self.assertEqual(content, expected_content)

    def test_stores_text(self):
        storage, client_mock = self._given_storage()

        storage.store_text('id1', 'content')

        self.assertEqual(client_mock.create_blob_from_text.call_count, 1)

    # noinspection PyTypeChecker
    @classmethod
    def _given_storage(cls, content=None):
        client_mock = MagicMock()
        storage = AzureStorage(account='account', key='key', container='name',
                               factory=lambda *args, **kwargs: client_mock)

        if content:
            build_blob = namedtuple('Blob', 'content')
            client_mock.get_blob_to_text.return_value = build_blob(content)

        return storage, client_mock
