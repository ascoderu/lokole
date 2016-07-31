from datetime import datetime

from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlockBlobService


class AzureBlob(object):
    def __init__(self, app=None):
        """
        :type app: flask.Flask

        """
        self.account_name = None
        self.account_key = None
        self.container = None
        self.upload_path = None
        self.download_path = None
        self.upload_format = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        :type app: flask.Flask

        """
        self.account_name = app.config.get('REMOTE_STORAGE_ACCOUNT_NAME')
        self.account_key = app.config.get('REMOTE_STORAGE_ACCOUNT_KEY')
        self.container = app.config.get('REMOTE_STORAGE_CONTAINER')
        self.upload_path = app.config.get('REMOTE_UPLOAD_PATH')
        self.download_path = app.config.get('REMOTE_DOWNLOAD_PATH')
        self.upload_format = app.config.get('REMOTE_UPLOAD_FORMAT')

        app.remote_storage = self

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
