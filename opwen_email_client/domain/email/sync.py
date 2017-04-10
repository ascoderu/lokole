from abc import ABCMeta
from abc import abstractmethod
from gzip import GzipFile
from tempfile import NamedTemporaryFile

from azure.common import AzureException
from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlockBlobService


class AzureAuth(object):
    def __init__(self, account, key, container):
        """
        :type account: str
        :type key: str
        :type container: str

        """
        self.account = account
        self.key = key
        self.container = container


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items):
        """
        :type items: collections.Iterable[T]
        :rtype items: collections.Iterable[str]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self):
        """
        :rtype: collections.Iterable[T]

        """
        raise NotImplementedError  # pragma: no cover


class AzureSync(Sync):
    def __init__(self, auth, download_locations, upload_locations, serializer):
        """
        :type auth: opwen_domain.sync.azure.AzureAuth
        :type download_locations: collections.Iterable[str]
        :type upload_locations: collections.Iterable[str]
        :type serializer: opwen_infrastructure.serialization.Serializer

        """
        self._auth = auth
        self._download_locations = list(download_locations)
        self._upload_locations = list(upload_locations)
        self._serializer = serializer

    def _create_client(self):
        """
        :rtype: azure.storage.blob.BlockBlobService

        """
        return BlockBlobService(self._auth.account, self._auth.key)

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
        :rtype bool

        """
        client = self._create_client()
        try:
            client.get_blob_to_stream(self._auth.container, blobname, stream)
        except AzureMissingResourceHttpError:
            return False
        else:
            return True

    def _upload_from_stream(self, blobname, stream):
        """
        :type blobname: str
        :type stream: io.IOBase

        """
        client = self._create_client()
        client.create_blob_from_stream(self._auth.container, blobname, stream)

    def _delete(self, blobname):
        """
        :type blobname: str

        """
        client = self._create_client()
        try:
            client.delete_blob(self._auth.container, blobname)
        except AzureException:
            pass

    @classmethod
    def _extract_root(cls, blob):
        """

        :type blob: azure.storage.blob.Blob
        :rtype: str

        """
        return blob.name.split('/')[0]

    def list_roots(self):
        """
        :rtype: collections.Iterable[str]

        """
        client = self._create_client()
        blobs = client.list_blobs(self._auth.container)
        return frozenset(map(self._extract_root, blobs))

    def download(self):
        for download_location in self._download_locations:
            with self._workspace() as workspace:
                if self._download_to_stream(download_location, workspace):
                    workspace.seek(0)
                    with self._open(workspace) as downloaded:
                        for line in downloaded:
                            yield self._serializer.deserialize(line)
            self._delete(download_location)

    def upload(self, items):
        uploaded_ids = []

        for upload_location, items_for_location in zip(self._upload_locations, items):
            upload_required = False

            with self._workspace() as workspace:
                with self._open(workspace, 'wb') as uploaded:
                    for item in items_for_location:
                        item = {key: value for (key, value) in item.items()
                                if value is not None}
                        serialized = self._serializer.serialize(item)
                        uploaded.write(serialized)
                        uploaded.write(b'\n')
                        upload_required = True
                        uploaded_ids.append(item.get('_uid'))

                if upload_required:
                    workspace.seek(0)
                    self._upload_from_stream(upload_location, workspace)
                else:
                    self._delete(upload_location)

        return uploaded_ids
