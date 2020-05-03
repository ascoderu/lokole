from glob import glob
from io import BytesIO
from os import mkdir
from os.path import join
from shutil import rmtree
from tarfile import TarInfo
from tempfile import mkdtemp
from typing import Dict
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from opwen_email_client.domain.email.sync import AzureSync
from opwen_email_client.domain.email.sync import Download
from opwen_email_client.util.serialization import JsonSerializer


class AzureSyncTests(TestCase):
    _test_compressions = ('gz', 'zstd')

    # noinspection PyTypeChecker
    def setUp(self):
        self._root_folder = mkdtemp()
        self.email_server_client_mock = Mock()
        self._container = 'compressedpackages'
        self.sync = AzureSync(container=self._container,
                              email_server_client=self.email_server_client_mock,
                              account_key='mock',
                              account_name=self._root_folder,
                              account_host=None,
                              account_secure=True,
                              provider='LOCAL',
                              compression='gz',
                              serializer=JsonSerializer())
        self._content_root = join(self._root_folder, self._container)
        mkdir(self._content_root)

    def tearDown(self):
        rmtree(self._root_folder)

    def assertUploadIs(self, expected: Dict[str, bytes], compression: str = ''):
        uploaded = glob(join(self._content_root, '*.{}'.format(compression or self.sync._compression)))

        self.assertEqual(len(uploaded), 1, 'Expected exactly one upload')

        infos = (Download(name=name, optional=False, type_='') for name in expected)

        with open(uploaded[0], 'rb') as buffer:
            with self.sync._open(buffer.name, 'r') as archive:
                for download, fobj in self.sync._get_file_from_download(archive, infos):
                    self.assertEqual(expected[download.name], fobj.read())

    def assertNoUpload(self):
        uploaded = glob(join(self._content_root, '*'))
        self.assertEqual(len(uploaded), 0, 'Expected no uploads')

    def given_download(self, payload: Dict[str, bytes], compression: str):
        resource_id = '{}.tar.{}'.format(uuid4(), compression)
        download_filename = join(self._content_root, resource_id)

        with self.sync._open(download_filename, 'w') as archive:
            for filename, content in payload.items():
                tarinfo = TarInfo(filename)
                tarinfo.size = len(content)
                archive.addfile(tarinfo, BytesIO(content))

        self.email_server_client_mock.download.return_value = resource_id

    def given_download_exception(self):
        self.email_server_client_mock.download.return_value = 'unknown'

    def test_upload(self):
        for compression in self._test_compressions:
            with self.subTest(compression=compression):
                self.sync._compression = compression
                self.sync.upload(items=[{'foo': 'bar'}], users=[])

                self.assertUploadIs({self.sync._emails_file: b'{"foo":"bar"}\n'}, compression)
                self.assertTrue(self.email_server_client_mock.upload.called)

    def test_upload_excludes_null_values(self):
        self.sync.upload(items=[{'foo': 0, 'bar': None}], users=[])

        self.assertUploadIs({self.sync._emails_file: b'{"foo":0}\n'})

    def test_upload_excludes_internal_values(self):
        self.sync.upload(items=[{'foo': 0, 'read': True, 'attachments': [{'_uid': '1', 'filename': 'foo.txt'}]}],
                         users=[])

        self.assertUploadIs({self.sync._emails_file: b'{"attachments":[{"filename":"foo.txt"}]' b',"foo":0}\n'})

    def test_upload_with_no_content_does_not_hit_network(self):
        self.sync.upload(items=[], users=[])

        self.assertNoUpload()
        self.assertFalse(self.email_server_client_mock.upload.called)

    def test_download(self):
        for compression in self._test_compressions:
            with self.subTest(compression=compression):
                self.given_download({self.sync._emails_file: b'{"foo":"bar"}\n{"baz":1}'}, compression)

                downloaded = list(self.sync.download())

                self.assertTrue(self.email_server_client_mock.download.called)
                self.assertEqual(len(downloaded), 2)
                self.assertIn({'foo': 'bar', '_type': 'email'}, downloaded)
                self.assertIn({'baz': 1, '_type': 'email'}, downloaded)

    def test_download_with_attachments(self):
        for compression in self._test_compressions:
            with self.subTest(compression=compression):
                self.given_download(
                    {
                        self.sync._emails_file: b'{"foo":"bar"}\n{"baz":1}', self.sync._attachments_file:
                        b'{"x":"y"}\n{"z":1}'
                    }, compression)

                downloaded = list(self.sync.download())

                self.assertTrue(self.email_server_client_mock.download.called)
                self.assertEqual(len(downloaded), 4)
                self.assertIn({'foo': 'bar', '_type': 'email'}, downloaded)
                self.assertIn({'baz': 1, '_type': 'email'}, downloaded)
                self.assertIn({'x': 'y', '_type': 'attachment'}, downloaded)
                self.assertIn({'z': 1, '_type': 'attachment'}, downloaded)

    def test_download_missing_resource(self):
        self.given_download_exception()

        downloaded = list(self.sync.download())

        self.assertEqual(downloaded, [])
