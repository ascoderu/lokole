from glob import glob
from io import BytesIO
from os import mkdir
from os.path import join
from shutil import rmtree
from tarfile import TarInfo
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from opwen_email_client.domain.email.sync import AzureSync
from opwen_email_client.util.serialization import JsonSerializer


class AzureSyncTests(TestCase):
    _test_compressions = ('gz', 'zstd')

    # noinspection PyTypeChecker
    def setUp(self):
        self._root_folder = mkdtemp()
        self.email_server_client_mock = Mock()
        self._container = 'compressedpackages'
        self.sync = AzureSync(
            container=self._container,
            email_server_client=self.email_server_client_mock,
            account_key='mock',
            account_name=self._root_folder,
            provider='LOCAL',
            compression='gz',
            serializer=JsonSerializer())
        self._content_root = join(self._root_folder, self._container)
        mkdir(self._content_root)

    def tearDown(self):
        rmtree(self._root_folder)

    def assertUploadIs(self, expected: bytes, compression: str = ''):
        uploaded = glob(join(
            self._content_root,
            '*.{}'.format(compression or self.sync._compression)))

        self.assertEqual(len(uploaded), 1, 'Expected exactly one upload')

        with open(uploaded[0], 'rb') as buffer:
            with self.sync._open(buffer.name, 'r') as archive:
                fobj = self.sync._get_file_from_download(
                    archive, self.sync._emails_file)
                self.assertEqual(expected, fobj.read())

    def assertNoUpload(self):
        uploaded = glob(join(self._content_root, '*'))
        self.assertEqual(len(uploaded), 0, 'Expected no uploads')

    def given_download(self, payload: bytes, compression: str):
        resource_id = '{}.tar.{}'.format(uuid4(), compression)
        download_filename = join(self._content_root, resource_id)

        with self.sync._open(download_filename, 'w') as archive:
            tarinfo = TarInfo(self.sync._emails_file)
            tarinfo.size = len(payload)
            archive.addfile(tarinfo, BytesIO(payload))

        self.email_server_client_mock.download.return_value = resource_id

    def given_download_exception(self):
        self.email_server_client_mock.download.return_value = 'unknown'

    def test_upload(self):
        for compression in self._test_compressions:
            with self.subTest(compression=compression):
                self.sync._compression = compression
                self.sync.upload(items=[{'foo': 'bar', 'read': True}])

                self.assertUploadIs(b'{"foo":"bar"}\n', compression)
                self.assertTrue(self.email_server_client_mock.upload.called)

    def test_upload_excludes_null_values(self):
        self.sync.upload(items=[{'foo': 0, 'bar': None}])

        self.assertUploadIs(b'{"foo":0}\n')

    def test_upload_with_no_content_does_not_hit_network(self):
        self.sync.upload(items=[])

        self.assertNoUpload()
        self.assertFalse(self.email_server_client_mock.upload.called)

    def test_download(self):
        for compression in self._test_compressions:
            with self.subTest(compression=compression):
                self.given_download(b'{"foo":"bar"}\n{"baz":1}', compression)

                downloaded = list(self.sync.download())

                self.assertTrue(self.email_server_client_mock.download.called)
                self.assertEqual(len(downloaded), 2)
                self.assertIn({'foo': 'bar'}, downloaded)
                self.assertIn({'baz': 1}, downloaded)

    def test_download_missing_resource(self):
        self.given_download_exception()

        downloaded = list(self.sync.download())

        self.assertEqual(downloaded, [])
