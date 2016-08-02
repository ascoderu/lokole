from unittest import TestCase

from azure.common import AzureMissingResourceHttpError

from utils.remotestorage import AzureBlob


class DownloadFailedBlockBlobService(object):
    def __getattribute__(self, item):
        if 'get_blob' in item:
            raise AzureMissingResourceHttpError('download failed', 404)
        return object.__getattribute__(self, item)


class TestAzureBlob(TestCase):
    def test_empty_upload_does_not_hit_network(self):
        blob = AzureBlob()
        blob.conn = lambda: self.fail('called remote service')
        blob.upload('/some/path/that/does/not/exist')

    def test_missing_download_returns_empty_bytes(self):
        blob = AzureBlob()
        blob.conn = lambda: DownloadFailedBlockBlobService()
        actual = blob.download()
        self.assertIsNone(actual)
