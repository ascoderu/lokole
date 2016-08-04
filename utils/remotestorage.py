from datetime import datetime
from os import path

from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlockBlobService

from utils.temporary import SafeNamedTemporaryFile


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
        self.filename_format = None

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
        self.filename_format = app.config.get('REMOTE_UPLOAD_FILENAME_FORMAT')

        app.remote_storage = self

    def conn(self):
        return BlockBlobService(self.account_name, self.account_key)

    def upload(self, path_to_payload):
        """
        :type path_to_payload: str

        """
        if not path_to_payload or not path.exists(path_to_payload):
            return

        filename = datetime.utcnow().strftime(self.filename_format)
        self.conn().create_blob_from_path(
            container_name=self.container,
            blob_name='/'.join((self.upload_path, filename)),
            file_path=path_to_payload)

    def download(self):
        """
        :rtype: str

        """
        try:
            with SafeNamedTemporaryFile('w', delete=False) as fobj:
                self.conn().get_blob_to_path(
                    container_name=self.container,
                    blob_name=self.download_path,
                    file_path=fobj.name)
            return fobj.name
        except AzureMissingResourceHttpError:
            return None
