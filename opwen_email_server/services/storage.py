from gzip import open as gzip_open
from json import loads
from typing import Callable
from typing import Iterable
from uuid import uuid4

from azure.storage.blob import BlockBlobService

from opwen_email_server.utils.serialization import to_json
from opwen_email_server.utils.temporary import create_tempfilename
from opwen_email_server.utils.temporary import removing


class _BaseAzureStorage(object):
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


class AzureTextStorage(_BaseAzureStorage):
    def store_text(self, resource_id: str, text: str):
        self._client.create_blob_from_text(self._container, resource_id, text)

    def fetch_text(self, resource_id: str) -> str:
        blob = self._client.get_blob_to_text(self._container, resource_id)
        return blob.content


class AzureFileStorage(_BaseAzureStorage):
    def store_file(self, resource_id: str, path: str):
        self._client.create_blob_from_path(self._container, resource_id, path)

    def fetch_file(self, resource_id: str) -> str:
        path = create_tempfilename()
        self._client.get_blob_to_path(self._container, resource_id, path)
        return path


class AzureObjectStorage(object):
    _encoding = 'utf-8'

    def __init__(self, file_storage: AzureFileStorage) -> None:
        self._file_storage = file_storage

    @property
    def container(self) -> str:
        return self._file_storage.container

    def store_objects(self, objs: Iterable[dict]) -> str:
        resource_id = str(uuid4())

        with removing(create_tempfilename()) as path:
            with gzip_open(path, 'wb') as fobj:
                for obj in objs:
                    serialized = to_json(obj)
                    encoded = serialized.encode(self._encoding)
                    fobj.write(encoded)
                    fobj.write(b'\n')
            self._file_storage.store_file(resource_id, path)

        return resource_id

    def fetch_objects(self, resource_id: str) -> Iterable[dict]:
        with removing(self._file_storage.fetch_file(resource_id)) as path:
            with gzip_open(path, 'rb') as fobj:
                for encoded in fobj:
                    serialized = encoded.decode(self._encoding)
                    obj = loads(serialized)
                    yield obj
