from abc import ABCMeta
from abc import abstractmethod
from gzip import GzipFile
from io import BytesIO
from io import TextIOBase
from tempfile import NamedTemporaryFile
from typing import Iterable
from typing import TypeVar

from azure.common import AzureException
from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import BlockBlobService, Blob

from opwen_email_client.util.serialization import Serializer

T = TypeVar('T')


class AzureAuth(object):
    def __init__(self, account: str, key: str, container: str):
        self.account = account
        self.key = key
        self.container = container


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items: Iterable[T]) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> Iterable[T]:
        raise NotImplementedError  # pragma: no cover


class AzureSync(Sync):
    def __init__(self, auth: AzureAuth, download_locations: Iterable[str],
                 upload_locations: Iterable[str], serializer: Serializer):
        self._auth = auth
        self._download_locations = list(download_locations)
        self._upload_locations = list(upload_locations)
        self._serializer = serializer

    def _create_client(self) -> BlockBlobService:
        return BlockBlobService(self._auth.account, self._auth.key)

    @classmethod
    def _workspace(cls) -> TextIOBase:
        return NamedTemporaryFile()

    @classmethod
    def _open(cls, fileobj: BytesIO, mode: str='rb') -> TextIOBase:
        return GzipFile(fileobj=fileobj, mode=mode)

    def _download_to_stream(self, blobname: str, stream: TextIOBase) -> bool:
        client = self._create_client()
        try:
            client.get_blob_to_stream(self._auth.container, blobname, stream)
        except AzureMissingResourceHttpError:
            return False
        else:
            return True

    def _upload_from_stream(self, blobname: str, stream: TextIOBase):
        client = self._create_client()
        client.create_blob_from_stream(self._auth.container, blobname, stream)

    def _delete(self, blobname: str):
        client = self._create_client()
        try:
            client.delete_blob(self._auth.container, blobname)
        except AzureException:
            pass

    def list_roots(self) -> Iterable[str]:
        client = self._create_client()
        blobs = client.list_blobs(self._auth.container)
        return frozenset(map(_extract_root, blobs))

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


def _extract_root(blob: Blob) -> str:
    return blob.name.split('/')[0]
