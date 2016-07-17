from unittest import TestCase

from utils.remote_storage import AzureBlob


class TestAzureBlob(TestCase):
    def test_empty_upload_does_not_hit_network(self):
        blob = AzureBlob('account', 'key', 'container', 'up', 'down', 'format')
        blob.conn = lambda: self.fail('called remote service')
        blob.upload(b'')
