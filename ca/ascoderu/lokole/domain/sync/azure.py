from datetime import datetime
from gzip import GzipFile
from tempfile import NamedTemporaryFile

from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlockBlobService

from ca.ascoderu.lokole.domain.sync.interfaces import Sync


class AzureSync(Sync):
    def __init__(self, account_name, account_key, container, download_location, upload_location, serializer):
        """
        :type account_name: str
        :type account_key: str
        :type container: str
        :type download_location: str
        :type upload_location: str
        :type serializer: ca.ascoderu.lokole.infrastructure.serialization.Serializer

        """
        self._account_name = account_name
        self._account_key = account_key
        self._container = container
        self._download_location = download_location
        self._serializer = serializer
        self.__upload_location = upload_location

    @property
    def _upload_location(self):
        """
        :rtype: str

        """
        return datetime.utcnow().strftime(self.__upload_location)

    def _create_client(self):
        """
        :rtype: azure.storage.blob.BlockBlobService

        """
        return BlockBlobService(self._account_name, self._account_key)

    @classmethod
    def _workspace(cls):
        """
        :rtype: io.TextIOBase

        """
        return NamedTemporaryFile()

    @classmethod
    def _open(cls, fileobj, mode='rb'):
        """
        :type fileobj: _io._IOBase
        :type mode: str
        :rtype: io.TextIOBase

        """
        return GzipFile(fileobj=fileobj, mode=mode)

    def _download_to_stream(self, blobname, stream):
        """
        :type blobname: str
        :type stream: io.IOBase

        """
        client = self._create_client()
        try:
            client.get_blob_to_stream(self._container, blobname, stream)
        except AzureMissingResourceHttpError:
            pass

    def _upload_from_stream(self, blobname, stream):
        """
        :type blobname: str
        :type stream: io.IOBase

        """
        client = self._create_client()
        client.create_blob_from_stream(self._container, blobname, stream)

    def download(self):
        with self._workspace() as workspace:
            self._download_to_stream(self._download_location, workspace)
            workspace.seek(0)
            with self._open(workspace) as downloaded:
                for line in downloaded:
                    yield self._serializer.deserialize(line)

    def upload(self, items):
        upload_required = False

        with self._workspace() as workspace:
            with self._open(workspace, 'wb') as uploaded:
                for item in items:
                    serialized = self._serializer.serialize(item)
                    uploaded.write(serialized)
                    uploaded.write(b'\n')
                    upload_required = True

            if upload_required:
                workspace.seek(0)
                self._upload_from_stream(self._upload_location, workspace)
