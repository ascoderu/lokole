from typing import Callable

from azure.storage.blob import BlockBlobService

from opwen_email_server.utils.temporary import create_tempfilename


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


class AzureStorage(_BaseAzureStorage):
    def store_text(self, resource_id: str, text: str):
        self._client.create_blob_from_text(self._container, resource_id, text)

    def fetch_text(self, resource_id: str) -> str:
        blob = self._client.get_blob_to_text(self._container, resource_id)
        return blob.content


class AzureFileStorage(_BaseAzureStorage):
    def fetch_file(self, resource_id: str) -> str:
        filename = create_tempfilename()
        self._client.get_blob_to_path(self._container, resource_id, filename)
        return filename
