from gzip import open as gzip_open
from json import loads
from typing import Callable
from typing import Iterable
from typing import Optional
from uuid import uuid4

from azure.storage.blob import BlockBlobService

from opwen_email_server.utils.log import LogMixin
from opwen_email_server.utils.serialization import to_json
from opwen_email_server.utils.temporary import create_tempfilename
from opwen_email_server.utils.temporary import removing


class _BaseAzureStorage(LogMixin):
    def __init__(self, account: str, key: str, container: str,
                 client: BlockBlobService=None,
                 factory: Callable[..., BlockBlobService]=BlockBlobService
                 ) -> None:

        self._account = account
        self._key = key
        self._container = container
        self.__client = client
        self._client_factory = factory

    @property
    def _client(self) -> BlockBlobService:
        if self.__client is not None:
            return self.__client
        client = self._client_factory(self._account, self._key)
        client.create_container(self._container)
        self.__client = client
        return client

    @property
    def container(self) -> str:
        return self._container

    def extra_log_args(self):
        yield 'container %s', self._container


class AzureTextStorage(_BaseAzureStorage):
    def store_text(self, resource_id: str, text: str):
        self.log_debug('storing %d characters at %s', len(text), resource_id)
        self._client.create_blob_from_text(self._container, resource_id, text)

    def fetch_text(self, resource_id: str) -> str:
        blob = self._client.get_blob_to_text(self._container, resource_id)
        text = blob.content
        self.log_debug('fetched %d characters from %s', len(text), resource_id)
        return text


class _AzureFileStorage(_BaseAzureStorage):
    def store_file(self, resource_id: str, path: str):
        self.log_debug('storing file %s at %s', path, resource_id)
        self._client.create_blob_from_path(self._container, resource_id, path)

    def fetch_file(self, resource_id: str) -> str:
        path = create_tempfilename()
        self._client.get_blob_to_path(self._container, resource_id, path)
        self.log_debug('fetched file %s from %s', path, resource_id)
        return path


class AzureObjectStorage(LogMixin):
    _encoding = 'utf-8'

    def __init__(self, account: str, key: str, container: str,
                 client: BlockBlobService=None,
                 factory: Callable[..., BlockBlobService]=BlockBlobService,
                 file_storage: _AzureFileStorage=None) -> None:
        self._file_storage = file_storage or _AzureFileStorage(
            account=account, key=key, container=container,
            client=client, factory=factory)

    @property
    def container(self) -> str:
        return self._file_storage.container

    def store_objects(self, objs: Iterable[dict]) -> Optional[str]:
        resource_id = str(uuid4())

        num_stored = 0
        with removing(create_tempfilename()) as path:
            with gzip_open(path, 'wb') as fobj:
                for obj in objs:
                    serialized = to_json(obj)
                    encoded = serialized.encode(self._encoding)
                    fobj.write(encoded)
                    fobj.write(b'\n')
                    num_stored += 1

            if num_stored > 0:
                self._file_storage.store_file(resource_id, path)

        self.log_debug('stored %d objects at %s', num_stored, resource_id)
        return resource_id if num_stored > 0 else None

    def fetch_objects(self, resource_id: str) -> Iterable[dict]:
        num_fetched = 0
        with removing(self._file_storage.fetch_file(resource_id)) as path:
            with gzip_open(path, 'rb') as fobj:
                for encoded in fobj:
                    serialized = encoded.decode(self._encoding)
                    obj = loads(serialized)
                    num_fetched += 1
                    yield obj
        self.log_debug('fetched %d objects from %s', num_fetched, resource_id)
