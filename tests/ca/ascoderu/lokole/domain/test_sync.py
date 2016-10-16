from io import BytesIO
from shutil import copyfileobj
from unittest import TestCase
from unittest.mock import Mock
from unittest.mock import patch

from azure.common import AzureMissingResourceHttpError

from ca.ascoderu.lokole.domain.sync.azure import AzureSync
from ca.ascoderu.lokole.infrastructure.serialization.json import JsonSerializer


class AzureSyncTests(TestCase):
    def setUp(self):
        self.sync = AzureSync(
            account_name='account_name',
            account_key='account_key',
            container='container',
            download_location='download_location',
            upload_location='upload_location',
            serializer=JsonSerializer())

    def assertUploadIs(self, actual, expected):
        """
        :type actual: _io._IOBase
        :type expected: bytes

        """
        with self.sync._open(actual) as uploaded:
            self.assertEqual(expected, uploaded.read())

    # noinspection PyMethodMayBeStatic
    def given_upload(self, create_client):
        """
        :type create_client: unittest.mock.Mock
        :rtype: io.BytesIO

        """
        mock_client = Mock()
        create_client.return_value = mock_client

        buffer = BytesIO()

        # noinspection PyUnusedLocal
        def side_effect(container, blobname, stream):
            copyfileobj(stream, buffer)
            buffer.seek(0)

        mock_client.create_blob_from_stream.side_effect = side_effect
        return buffer

    def given_download(self, payload, create_client):
        """
        :type payload: bytes
        :type create_client: unittest.mock.Mock

        """
        mock_client = Mock()
        create_client.return_value = mock_client

        buffer = BytesIO()
        with self.sync._open(buffer, 'wb') as fobj:
            fobj.write(payload)
        buffer.seek(0)

        # noinspection PyUnusedLocal
        def side_effect(container, blobname, stream):
            copyfileobj(buffer, stream)

        mock_client.get_blob_to_stream.side_effect = side_effect

    # noinspection PyMethodMayBeStatic
    def given_download_exception(self, create_client):
        """
        :type create_client: unittest.mock.Mock

        """
        mock_client = Mock()
        create_client.return_value = mock_client
        mock_client.get_blob_to_stream.side_effect = AzureMissingResourceHttpError('injected error', 404)

    def test_create_client(self):
        client = self.sync._create_client()

        self.assertIsNotNone(client)

    @patch('ca.ascoderu.lokole.domain.sync.azure.AzureSync._create_client')
    def test_upload(self, create_client):
        uploaded = self.given_upload(create_client)

        self.sync.upload([{'foo': 'bar'}])

        self.assertUploadIs(uploaded, b'{"foo":"bar"}\n')

    @patch('ca.ascoderu.lokole.domain.sync.azure.AzureSync._create_client')
    def test_upload_with_no_content_does_not_hit_network(self, create_client):
        create_client.return_value = Mock()

        self.sync.upload(items=[])

        self.assertFalse(create_client.return_value.create_blob_from_stream.called)

    @patch('ca.ascoderu.lokole.domain.sync.azure.AzureSync._create_client')
    def test_download(self, create_client):
        self.given_download(b'{"foo":"bar"}\n{"baz":1}', create_client)

        downloaded = list(self.sync.download())

        self.assertEqual(len(downloaded), 2)
        self.assertIn({'foo': 'bar'}, downloaded)
        self.assertIn({'baz': 1}, downloaded)

    @patch('ca.ascoderu.lokole.domain.sync.azure.AzureSync._create_client')
    def test_download_missing_resource(self, create_client):
        self.given_download_exception(create_client)

        downloaded = list(self.sync.download())

        self.assertEqual(downloaded, [])
