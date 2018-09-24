from io import BytesIO
from shutil import copyfileobj
from unittest import TestCase
from unittest.mock import Mock

from azure.common import AzureMissingResourceHttpError

from opwen_email_client.domain.email.sync import AzureSync
from opwen_email_client.util.serialization import JsonSerializer


class AzureSyncTests(TestCase):
    # noinspection PyTypeChecker
    def setUp(self):
        self.azure_client_mock = Mock()
        self.email_server_client_mock = Mock()
        self.sync = AzureSync(
            container='container',
            email_server_client=self.email_server_client_mock,
            account_key='mock',
            account_name='mock',
            azure_client=self.azure_client_mock,
            serializer=JsonSerializer())

    def assertUploadIs(self, actual: BytesIO, expected: bytes):
        with self.sync._open(actual) as uploaded:
            self.assertEqual(expected, uploaded.read())

    def given_upload(self) -> BytesIO:
        buffer = BytesIO()

        # noinspection PyUnusedLocal
        def side_effect(container, blobname, stream):
            copyfileobj(stream, buffer)
            buffer.seek(0)

        self.azure_client_mock.create_blob_from_stream.side_effect = side_effect
        return buffer

    def given_download(self, payload: bytes):
        buffer = BytesIO()
        with self.sync._open(buffer, 'wb') as fobj:
            fobj.write(payload)
        buffer.seek(0)

        # noinspection PyUnusedLocal
        def side_effect(container, blobname, stream):
            copyfileobj(buffer, stream)

        self.email_server_client_mock.download.return_value = ('id', 'folder')
        self.azure_client_mock.get_blob_to_stream.side_effect = side_effect

    def given_download_exception(self):
        error = AzureMissingResourceHttpError('injected error', 404)
        self.email_server_client_mock.download.return_value = ('id', 'folder')
        self.azure_client_mock.get_blob_to_stream.side_effect = error

    def test_upload(self):
        uploaded = self.given_upload()

        self.sync.upload(items=[{'foo': 'bar', 'read': True}])

        self.assertUploadIs(uploaded, b'{"foo":"bar"}\n')
        self.assertTrue(self.email_server_client_mock.upload.called)

    def test_upload_excludes_null_values(self):
        uploaded = self.given_upload()

        self.sync.upload(items=[{'foo': 0, 'bar': None}])

        self.assertUploadIs(uploaded, b'{"foo":0}\n')

    def test_upload_with_no_content_does_not_hit_network(self):
        self.sync.upload(items=[])

        self.assertFalse(self.azure_client_mock.create_blob_from_stream.called)
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
