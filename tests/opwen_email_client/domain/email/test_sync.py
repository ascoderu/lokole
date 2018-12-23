from glob import glob
from os import mkdir
from os.path import join
from shutil import rmtree
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from opwen_email_client.domain.email.sync import AzureSync
from opwen_email_client.util.serialization import JsonSerializer


class AzureSyncTests(TestCase):
    # noinspection PyTypeChecker
    def setUp(self):
        self._root_folder = mkdtemp()
        self.email_server_client_mock = Mock()
        self._upload_folder = 'uploads'
        self._download_folder = 'downloads'
        self.sync = AzureSync(
            container=self._upload_folder,
            email_server_client=self.email_server_client_mock,
            account_key='mock',
            account_name=self._root_folder,
            provider='LOCAL',
            serializer=JsonSerializer())
        mkdir(join(self._root_folder, self._download_folder))

    def tearDown(self):
        rmtree(self._root_folder)

    def assertUploadIs(self, expected: bytes):
        uploaded = glob(join(self._root_folder, self._upload_folder, '*'))
        self.assertEqual(len(uploaded), 1, 'Expected exactly one upload')

        with open(uploaded[0], 'rb') as buffer:
            with self.sync._open(buffer, 'r', 'archive') as archive:
                fobj = self.sync._get_file_from_download(
                    archive, self.sync._emails_file)
                self.assertEqual(expected, fobj.read())

    def assertNoUpload(self):
        uploaded = glob(join(self._root_folder, self._upload_folder, '*'))
        self.assertEqual(len(uploaded), 0, 'Expected no uploads')

    def given_download(self, payload: bytes):
        with NamedTemporaryFile() as fobj:
            fobj.write(payload)

            resource_id = str(uuid4())
            download_filename = join(
                self._root_folder, self._download_folder, resource_id)

            with open(download_filename, 'wb') as buffer:
                with self.sync._open(buffer, 'w', 'tar.gz') as archive:
                    self.sync._add_file_to_upload(
                        archive, self.sync._emails_file, fobj)

        self.email_server_client_mock.download.return_value = (
            resource_id,
            self._download_folder)

    def given_download_exception(self):
        self.email_server_client_mock.download.return_value = (
            'unknown-resource', self._download_folder)

    def test_upload(self):
        self.sync.upload(items=[{'foo': 'bar', 'read': True}])

        self.assertUploadIs(b'{"foo":"bar"}\n')
        self.assertTrue(self.email_server_client_mock.upload.called)

    def test_upload_excludes_null_values(self):
        self.sync.upload(items=[{'foo': 0, 'bar': None}])

        self.assertUploadIs(b'{"foo":0}\n')

    def test_upload_with_no_content_does_not_hit_network(self):
        self.sync.upload(items=[])

        self.assertNoUpload()
        self.assertFalse(self.email_server_client_mock.upload.called)

    def test_download(self):
        self.given_download(b'{"foo":"bar"}\n{"baz":1}')

        downloaded = list(self.sync.download())

        self.assertTrue(self.email_server_client_mock.download.called)
        self.assertEqual(len(downloaded), 2)
        self.assertIn({'foo': 'bar'}, downloaded)
        self.assertIn({'baz': 1}, downloaded)

    def test_download_missing_resource(self):
        self.given_download_exception()

        downloaded = list(self.sync.download())

        self.assertEqual(downloaded, [])
