from unittest import TestCase

from azure.common import AzureMissingResourceHttpError

from utils.remote_storage import AzureBlob


class DownloadFailedBlockBlobService(object):
    @classmethod
    def get_blob_to_bytes(cls, *args, **kwargs):
        raise AzureMissingResourceHttpError('download failed', 404)


class TestAzureBlob(TestCase):
    def test_empty_upload_does_not_hit_network(self):
        blob = AzureBlob()
        blob.conn = lambda: self.fail('called remote service')
        blob.upload(b'')

    def test_missing_download_returns_empty_bytes(self):
        blob = AzureBlob()
        blob.conn = lambda: DownloadFailedBlockBlobService()
        actual = blob.download()
        self.assertEqual(actual, b'')
