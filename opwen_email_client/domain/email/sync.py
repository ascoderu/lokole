from abc import ABCMeta
from abc import abstractmethod
from gzip import GzipFile
from io import BytesIO
from io import TextIOBase
from tempfile import NamedTemporaryFile
from typing import Iterable
from typing import TypeVar
from uuid import uuid4

from azure.common import AzureMissingResourceHttpError
from azure.storage.blob import Blob
from azure.storage.blob import BlockBlobService

from opwen_email_client.domain.email.client import EmailServerClient
from opwen_email_client.util.serialization import Serializer

T = TypeVar('T')


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items: Iterable[T]) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> Iterable[T]:
        raise NotImplementedError  # pragma: no cover


class AzureSync(Sync):
    def __init__(self, container: str, serializer: Serializer,
                 azure_client: BlockBlobService,
                 email_server_client: EmailServerClient):

        self._container = container
        self._serializer = serializer
        self._azure_client = azure_client
        self._email_server_client = email_server_client

    @classmethod
    def _workspace(cls) -> TextIOBase:
        return NamedTemporaryFile()

    @classmethod
    def _open(cls, fileobj: BytesIO, mode: str='rb') -> TextIOBase:
        return GzipFile(fileobj=fileobj, mode=mode)

    def _download_to_stream(self, blobname: str, container: str,
                            stream: TextIOBase) -> bool:

        try:
            self._azure_client.get_blob_to_stream(container, blobname, stream)
        except AzureMissingResourceHttpError:
            return False
        else:
            return True

    def _upload_from_stream(self, blobname: str, stream: TextIOBase):
        self._azure_client.create_blob_from_stream(self._container,
                                                   blobname, stream)

    def download(self):
        resource_id, container = self._email_server_client.download()

        with self._workspace() as workspace:
            if self._download_to_stream(resource_id, container, workspace):
                workspace.seek(0)
                with self._open(workspace) as downloaded:
                    for line in downloaded:
                        yield self._serializer.deserialize(line)

    def upload(self, items):
        uploaded_ids = []
        upload_location = str(uuid4())

        with self._workspace() as workspace:
            with self._open(workspace, 'wb') as uploaded:
                for item in items:
                    item = {key: value for (key, value) in item.items()
                            if value is not None}
                    serialized = self._serializer.serialize(item)
                    uploaded.write(serialized)
                    uploaded.write(b'\n')
                    uploaded_ids.append(item.get('_uid'))

            if uploaded_ids:
                workspace.seek(0)
                self._upload_from_stream(upload_location, workspace)
                self._email_server_client.upload(upload_location,
                                                 self._container)

        return uploaded_ids


def _extract_root(blob: Blob) -> str:
    return blob.name.split('/')[0]
