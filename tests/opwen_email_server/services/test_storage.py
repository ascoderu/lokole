from io import BytesIO
from os import listdir
from os import mkdir
from os import remove
from os.path import isdir
from os.path import join
from shutil import rmtree
from tarfile import TarInfo
from tarfile import open as tarfile_open
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp
from unittest import TestCase

from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureObjectsStorage
from opwen_email_server.services.storage import AzureTextStorage


class AzureTextStorageTests(TestCase):
    def test_stores_fetches_and_deletes_text(self):
        resource_id, expected_content = 'id1', 'some content'

        self._storage.store_text(resource_id, expected_content)
        actual_content = self._storage.fetch_text(resource_id)

        self.assertEqual(actual_content, expected_content)

        self._storage.delete(resource_id)
        with self.assertRaises(ObjectDoesNotExistError):
            self._storage.fetch_text(resource_id)

    def test_list(self):
        self._storage.store_text('resource1', 'a')
        self._storage.store_text('resource2.txt.gz', 'b')
        self.assertEqual(sorted(self._storage.iter()),
                         sorted(['resource1.txt.gz', 'resource2.txt.gz']))

        self._storage.delete('resource2')
        self.assertEqual(sorted(self._storage.iter()),
                         sorted(['resource1.txt.gz']))

    def test_ensure_exists(self):
        self.assertFalse(isdir(join(self._folder, self._container)))
        self._storage.ensure_exists()
        self.assertTrue(isdir(join(self._folder, self._container)))

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        self._storage = AzureTextStorage(
            account=self._folder, key='key',
            container=self._container, provider='LOCAL')

    def tearDown(self):
        rmtree(self._folder)


class AzureFileStorageTests(TestCase):
    def test_stores_fetches_and_deletes_file(self):
        resource_id, expected_content = 'id1', 'some content'
        self._given_file(resource_id, expected_content)

        actual_path = self._storage.fetch_file(resource_id)

        self.assertFileContains(actual_path, expected_content)

        self._storage.delete(resource_id)
        with self.assertRaises(ObjectDoesNotExistError):
            self._storage.fetch_file(resource_id)

    def assertFileContains(self, path: str, content: str):
        with open(path, encoding='utf-8') as fobj:
            self.assertEqual(fobj.read(), content)

    def _given_file(self, resource_id: str, expected_content: str):
        with NamedTemporaryFile('w', encoding='utf-8', delete=False) as fobj:
            fobj.write(expected_content)
            fobj.seek(0)
            self._storage.store_file(resource_id, fobj.name)
            self._extra_files.add(fobj.name)

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        self._storage = AzureFileStorage(
            account=self._folder, key='key',
            container=self._container, provider='LOCAL')
        self._extra_files = set()

    def tearDown(self):
        rmtree(self._folder)
        for path in self._extra_files:
            remove(path)


class AzureObjectsStorageTests(TestCase):
    def test_fetches_jsonl_objects(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"foo":"bar"}\n{"baz":[1,2,3]}'
        self._given_resource(resource_id, name, lines)

        objs = list(self._storage.fetch_objects(resource_id, name))

        self.assertEqual(objs, [{'foo': 'bar'}, {'baz': [1, 2, 3]}])

    def test_fetches_missing_file(self):
        with self.assertRaises(ObjectDoesNotExistError):
            list(self._storage.fetch_objects('missing', 'file'))

    def test_fetches_missing_archive_member(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"foo":"bar"}\n{"baz":[1,2,3]}'
        self._given_resource(resource_id, name, lines)

        with self.assertRaises(ObjectDoesNotExistError):
            list(self._storage.fetch_objects(resource_id, 'missing-tar'))

    def test_fetches_json_objects(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"emails":[\n{"foo":"bar"},\n{"baz":[1,2,3]}\n]}'
        self._given_resource(resource_id, name, lines)

        objs = list(self._storage.fetch_objects(resource_id, name))

        self.assertEqual(objs, [{'foo': 'bar'}, {'baz': [1, 2, 3]}])

    def test_handles_corrupted_jsonl_entries(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"foo":"bar"}\n{"corrupted":1,]}\n{"baz":[1,2,3]}'
        self._given_resource(resource_id, name, lines)

        objs = list(self._storage.fetch_objects(resource_id, name))

        self.assertEqual(objs, [{'foo': 'bar'}, {'baz': [1, 2, 3]}])

    def test_stores_objects(self):
        resource_id = 'file.tar.gz'
        name = 'file'
        objs = [{'foo': 'bar'}, {'baz': [1, 2, 3]}]

        resource_id = self._storage.store_objects((name, objs), resource_id)

        self.assertIsNotNone(resource_id)
        self.assertContainerHasNumFiles(1)

    def test_does_not_create_file_without_objects(self):
        resource_id = 'file.tar.gz'
        name = 'file'
        objs = []

        resource_id = self._storage.store_objects((name, objs), resource_id)

        self.assertIsNone(resource_id)
        self.assertContainerHasNumFiles(0)

    def assertContainerHasNumFiles(self, count: int):
        path = join(self._folder, self._container)
        self.assertEqual(len(listdir(path)), count)

    def _given_resource(self, resource_id: str, name: str, lines: bytes):
        client = self._storage._file_storage._client
        buffer = BytesIO()
        with tarfile_open(mode='w:gz', fileobj=buffer) as archive:
            tarinfo = TarInfo(name)
            tarinfo.size = len(lines)
            archive.addfile(tarinfo, BytesIO(lines))
        buffer.seek(0)
        client.upload_object_via_stream(buffer, resource_id)

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        mkdir(join(self._folder, self._container))
        self._storage = AzureObjectsStorage(
            file_storage=AzureFileStorage(
                account=self._folder,
                key='unused',
                container=self._container,
                provider='LOCAL'))

    def tearDown(self):
        rmtree(self._folder)


class AzureObjectStorageTests(TestCase):
    def test_roundtrip(self):
        given = {'a': 1}
        resource_id = '123'

        self._storage.store_object(resource_id, given)
        actual = self._storage.fetch_object(resource_id)

        self.assertEqual(given, actual)

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        mkdir(join(self._folder, self._container))
        self._storage = AzureObjectStorage(
            text_storage=AzureTextStorage(
                account=self._folder,
                key='unused',
                container=self._container,
                provider='LOCAL'))

    def tearDown(self):
        rmtree(self._folder)
