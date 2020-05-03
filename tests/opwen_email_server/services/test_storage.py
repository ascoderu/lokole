from io import BytesIO
from os import listdir
from os import mkdir
from os import remove
from os.path import isdir
from os.path import join
from pathlib import Path
from shutil import rmtree
from tarfile import TarInfo
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import PropertyMock
from unittest.mock import patch

from libcloud.storage.types import ContainerAlreadyExistsError
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError
from xtarfile import open as tarfile_open

from opwen_email_server.services.storage import AzureFileStorage
from opwen_email_server.services.storage import AzureObjectStorage
from opwen_email_server.services.storage import AzureObjectsStorage
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.serialization import from_jsonl_bytes
from opwen_email_server.utils.serialization import to_jsonl_bytes
from opwen_email_server.utils.temporary import create_tempfilename
from opwen_email_server.utils.temporary import removing
from opwen_email_server.utils.unique import NewGuid
from tests.opwen_email_server.helpers import throw


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
        self._storage.store_text('pa.th/to/re.sou.rce.txt.gz', 'b')
        self.assertEqual(sorted(self._storage.iter()), sorted(['resource1', 'resource2', 'pa.th/to/re.sou.rce']))

        self._storage.delete('resource2')
        self._storage.delete('pa.th/to/re.sou.rce')
        self.assertEqual(sorted(self._storage.iter()), sorted(['resource1']))

    def test_list_with_prefix(self):
        self._storage.store_text('one/a', 'a')
        self._storage.store_text('one/b.txt.gz', 'b')
        self._storage.store_text('two/c.txt.gz', 'c')
        self._storage.store_text('two/d', 'd')
        self._storage.store_text('two/e', 'e')
        self._storage.store_text('f', 'f')
        self.assertEqual(sorted(self._storage.iter('one/')), sorted(['a', 'b']))
        self.assertEqual(sorted(self._storage.iter('two/')), sorted(['c', 'd', 'e']))

    def test_ensure_exists(self):
        self.assertFalse(isdir(join(self._folder, self._container)))
        self._storage.ensure_exists()
        self.assertTrue(isdir(join(self._folder, self._container)))

    def test_handles_race_condition_when_creating_container(self):
        with patch.object(self._storage, '_driver', new_callable=PropertyMock) as driver:
            container = {'get_was_called': False}

            # noinspection PyUnusedLocal
            def get_container(*args, **kwargs):
                if not container['get_was_called']:
                    container['get_was_called'] = True
                    # noinspection PyTypeChecker
                    raise ContainerDoesNotExistError(None, driver, self._container)

                return container

            # noinspection PyTypeChecker
            driver.create_container.side_effect = throw(ContainerAlreadyExistsError(None, driver, self._container))
            driver.get_container.side_effect = get_container

            self.assertIs(self._storage._client._wrapped, container)

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        self._storage = AzureTextStorage(
            account=self._folder,
            key='key',
            container=self._container,
            provider='LOCAL',
        )

    def tearDown(self):
        rmtree(self._folder)


class AzureTextStorageCaseInsensitiveTests(TestCase):
    def test_stores_fetches_and_deletes_text(self):
        self._storage.store_text('iD1', 'some content')
        actual_content = self._storage.fetch_text('Id1')

        self.assertEqual(actual_content, 'some content')

        self._storage.delete('id1')
        with self.assertRaises(ObjectDoesNotExistError):
            self._storage.fetch_text('id1')

    def test_list_with_prefix(self):
        self._storage.store_text('One/a', 'a')
        self._storage.store_text('one/b.txt.gz', 'b')
        self._storage.store_text('tWo/c.txt.gz', 'c')
        self._storage.store_text('twO/d', 'd')
        self._storage.store_text('two/e', 'e')
        self._storage.store_text('f', 'f')
        self.assertEqual(sorted(self._storage.iter('one/')), sorted(['a', 'b']))
        self.assertEqual(sorted(self._storage.iter('two/')), sorted(['c', 'd', 'e']))

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        self._storage = AzureTextStorage(
            account=self._folder,
            key='key',
            container=self._container,
            provider='LOCAL',
            case_sensitive=False,
        )

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

        self._storage.delete(resource_id)

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
            account=self._folder,
            key='key',
            container=self._container,
            provider='LOCAL',
        )
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

        objs = list(self._storage.fetch_objects(resource_id, (name, from_jsonl_bytes)))

        self.assertEqual(objs, [{'foo': 'bar'}, {'baz': [1, 2, 3]}])

    def test_fetches_missing_file(self):
        with self.assertRaises(ObjectDoesNotExistError):
            list(self._storage.fetch_objects('missing', ('file', from_jsonl_bytes)))

    def test_fetches_missing_archive_member(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"foo":"bar"}\n{"baz":[1,2,3]}'
        self._given_resource(resource_id, name, lines)

        with self.assertRaises(ObjectDoesNotExistError):
            list(self._storage.fetch_objects(resource_id, ('missing-tar', from_jsonl_bytes)))

    def test_fetches_json_objects(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"emails":[\n{"foo":"bar"},\n{"baz":[1,2,3]}\n]}'
        self._given_resource(resource_id, name, lines)

        objs = list(self._storage.fetch_objects(resource_id, (name, from_jsonl_bytes)))

        self.assertEqual(objs, [{'foo': 'bar'}, {'baz': [1, 2, 3]}])

    def test_handles_corrupted_jsonl_entries(self):
        resource_id = '3d2bfa80-18f7-11e7-93ae-92361f002671.tar.gz'
        name = 'file'
        lines = b'{"foo":"bar"}\n{"corrupted":1,]}\n{"baz":[1,2,3]}'
        self._given_resource(resource_id, name, lines)

        objs = list(self._storage.fetch_objects(resource_id, (name, from_jsonl_bytes)))

        self.assertEqual(objs, [{'foo': 'bar'}, {'baz': [1, 2, 3]}])

    def test_stores_objects(self):
        name = 'file'
        objs = [{'foo': 'bar'}, {'baz': [1, 2, 3]}]

        resource_id = self._storage.store_objects((name, objs, to_jsonl_bytes))

        self.assertIsNotNone(resource_id)
        self.assertContainerHasNumFiles(1, suffix='.tar.zstd')

    def test_stores_objects_with_explicit_compression(self):
        name = 'file'
        objs = [{'foo': 'bar'}, {'baz': [1, 2, 3]}]

        resource_id = self._storage.store_objects((name, objs, to_jsonl_bytes), 'gz')

        self.assertIsNotNone(resource_id)
        self.assertContainerHasNumFiles(1, suffix='.tar.gz')

    def test_does_not_create_file_without_objects(self):
        name = 'file'
        objs = []

        resource_id = self._storage.store_objects((name, objs, to_jsonl_bytes), 'gz')

        self.assertIsNone(resource_id)
        self.assertContainerHasNumFiles(0)

    def test_deletes_objects(self):
        name = 'file'
        objs = [{'foo': 'bar'}, {'baz': [1, 2, 3]}]

        resource_id = self._storage.store_objects((name, objs, to_jsonl_bytes))
        self._storage.delete(resource_id)

        self.assertContainerHasNumFiles(0)

    def assertContainerHasNumFiles(self, count: int, suffix: str = ''):
        container_files = listdir(join(self._folder, self._container))
        matches = [entry for entry in container_files if entry.endswith(suffix)]

        self.assertEqual(
            len(matches),
            count,
            f'Container does not have {count} files ending with "{suffix}"; '
            f'all files in container are: {", ".join(container_files)}',
        )

    def _given_resource(self, resource_id: str, name: str, lines: bytes):
        client = self._storage._file_storage._client
        mode = f'w:{Path(resource_id).suffix[1:]}'
        with removing(create_tempfilename(resource_id)) as buffer_path:
            with tarfile_open(buffer_path, mode) as archive:
                tarinfo = TarInfo(name)
                tarinfo.size = len(lines)
                archive.addfile(tarinfo, BytesIO(lines))
            client.upload_object(buffer_path, resource_id)

    def setUp(self):
        self._folder = mkdtemp()
        self._container = 'container'
        mkdir(join(self._folder, self._container))
        self._storage = AzureObjectsStorage(
            file_storage=AzureFileStorage(
                account=self._folder,
                key='unused',
                container=self._container,
                provider='LOCAL',
            ),
            resource_id_source=NewGuid(0),
        )

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
            account=self._folder,
            key='unused',
            container=self._container,
            provider='LOCAL',
        )

    def tearDown(self):
        rmtree(self._folder)
