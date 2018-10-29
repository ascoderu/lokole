from abc import ABCMeta
from abc import abstractmethod
from gzip import GzipFile
from io import TextIOBase
from tempfile import NamedTemporaryFile
from typing import IO
from typing import Iterable
from typing import TypeVar
from uuid import uuid4

from cached_property import cached_property
from libcloud.storage.base import StorageDriver
from libcloud.storage.providers import Provider
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_client.domain.email.client import EmailServerClient
from opwen_email_client.util.serialization import Serializer

T = TypeVar('T')

EXCLUDED_FIELDS = frozenset([
    'read',
])


class Sync(metaclass=ABCMeta):
    @abstractmethod
    def upload(self, items: Iterable[T]) -> Iterable[str]:
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def download(self) -> Iterable[T]:
        raise NotImplementedError  # pragma: no cover


class AzureSync(Sync):
    def __init__(self, container: str, serializer: Serializer,
                 account_name: str, account_key: str,
                 email_server_client: EmailServerClient,
                 provider: str):

        self._container = container
        self._serializer = serializer
        self._account = account_name
        self._key = account_key
        self._email_server_client = email_server_client
        self._provider = getattr(Provider, provider)

    @cached_property
    def _azure_client(self) -> StorageDriver:
        driver = get_driver(self._provider)
        client = driver(self._account, self._key)
        try:
            client.get_container(self._container)
        except ContainerDoesNotExistError:
            client.create_container(self._container)
        return client

    @classmethod
    def _workspace(cls) -> TextIOBase:
        return NamedTemporaryFile()

    @classmethod
    def _open(cls, fileobj: IO, mode: str = 'rb') -> GzipFile:
        return GzipFile(fileobj=fileobj, mode=mode)

    def _download_to_stream(self, blobname: str, container: str,
                            stream: IO) -> bool:

        try:
            container = self._azure_client.get_container(container)
            resource = container.get_object(blobname)
        except ObjectDoesNotExistError:
            return False
        else:
            for chunk in resource.as_stream():
                stream.write(chunk)
            return True

    def _upload_from_stream(self, blobname: str, stream: TextIOBase):
        container = self._azure_client.get_container(self._container)
        container.upload_object_via_stream(stream, blobname)

    def download(self):
        resource_id, container = self._email_server_client.download()
        if not resource_id or not container:
            return

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
                            if value is not None
                            and key not in EXCLUDED_FIELDS}
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
