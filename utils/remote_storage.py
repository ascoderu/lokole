from datetime import datetime

# noinspection PyPackageRequirements
from azure.storage.blob import BlockBlobService


class AzureBlob(object):
    def __init__(self, account_name, account_key, container,
                 upload_path, download_path, upload_format):
        self.account_name = account_name
        self.account_key = account_key
        self.container = container
        self.upload_path = upload_path
        self.download_path = download_path
        self.upload_format = upload_format

    def conn(self):
        return BlockBlobService(self.account_name, self.account_key)

    def upload(self, payload):
        if not payload:
            return

        upload_name = datetime.utcnow().strftime(self.upload_format)
        upload_path = '%s/%s' % (self.upload_path, upload_name)
        self.conn().create_blob_from_bytes(self.container, upload_path, payload)

    def download(self):
        return self.conn().get_blob_to_bytes(self.container, self.download_path)
