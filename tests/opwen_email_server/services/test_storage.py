from collections import namedtuple
from os import remove
from unittest import TestCase
from unittest.mock import MagicMock

from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureStorage


class AzureStorageTests(TestCase):
    def test_creates_container_only_once(self):
        expected_content = 'some content'
        storage, client_mock = self.given_storage(expected_content)

        storage.fetch_text('id1')
        storage.fetch_text('id1')

        self.assertEqual(client_mock.create_container.call_count, 1)

    def test_fetches_text(self):
        expected_content = 'some content'
        storage, client_mock = self.given_storage(expected_content)

        content = storage.fetch_text('id1')

        self.assertEqual(client_mock.get_blob_to_text.call_count, 1)
        self.assertEqual(content, expected_content)

    def test_stores_text(self):
        storage, client_mock = self.given_storage()

        storage.store_text('id1', 'content')

        self.assertEqual(client_mock.create_blob_from_text.call_count, 1)

    # noinspection PyTypeChecker
    @classmethod
    def given_storage(cls, content=None):
        client_mock = MagicMock()
        storage = AzureStorage(account='account', key='key', container='name',
                               factory=lambda *args, **kwargs: client_mock)

        if content:
            build_blob = namedtuple('Blob', 'content')
            client_mock.get_blob_to_text.return_value = build_blob(content)

        return storage, client_mock


class AzureFileStorageTests(TestCase):
    def test_fetches_file(self):
        storage, client_mock = self.given_storage()

        self.when_fetching_file(storage)

        self.assertEqual(client_mock.get_blob_to_path.call_count, 1)

    # noinspection PyTypeChecker
    @classmethod
    def given_storage(cls):
        client_mock = MagicMock()
        storage = AzureFileStorage(
            account='account', key='key', container='name',
            factory=lambda *args, **kwargs: client_mock)

        return storage, client_mock

    def when_fetching_file(self, storage):
        filename = storage.fetch_file('id1')
        self._filenames.add(filename)
        return filename

    def setUp(self):
        self._filenames = set()

    def tearDown(self):
        for filename in self._filenames:
            remove(filename)
