from datetime import datetime

from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlockBlobService


class AzureBlob(object):
    def __init__(self, account_name, account_key, container,
                 upload_path, download_path, upload_format):
        """
        :type account_name: str
        :type account_key: str
        :type container: str
        :type upload_path: str
        :type download_path: str
        :type upload_format: str

        """
        self.account_name = account_name
        self.account_key = account_key
        self.container = container
        self.upload_path = upload_path
        self.download_path = download_path
        self.upload_format = upload_format

    def conn(self):
        return BlockBlobService(self.account_name, self.account_key)

    def upload(self, payload):
        """
        :type payload: bytes

        """
        if not payload:
            return

        upload_name = datetime.utcnow().strftime(self.upload_format)
        upload_path = '%s/%s' % (self.upload_path, upload_name)
        self.conn().create_blob_from_bytes(self.container, upload_path, payload)

    def download(self):
        """
        :rtype: bytes

        """
        try:
            return self.conn().get_blob_to_bytes(self.container,
                                                 self.download_path)
        except AzureMissingResourceHttpError:
            return b''
