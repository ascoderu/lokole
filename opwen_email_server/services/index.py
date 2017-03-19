from typing import Callable
from typing import Generic
from typing import Iterable
from typing import Mapping
from typing import TypeVar

from azure.storage.table import TableBatch
from azure.storage.table import TableService

T = TypeVar('T')


class AzureIndex(Generic[T]):
    def __init__(self, account: str, key: str,
                 tables: Mapping[str, Callable[[T], Iterable[str]]],
                 client: TableService=None,
                 client_factory: Callable[..., TableService]=TableService,
                 batch_factory: Callable[..., TableBatch]=TableBatch):

        self._account = account
        self._key = key
        self._tables = dict(tables.items())
        self.__client = client
        self._client_factory = client_factory
        self._batch_factory = batch_factory

    @property
    def _client(self) -> TableService:
        if self.__client is not None:
            return self.__client
        client = self._client_factory(self._account, self._key)
        for table in self._tables:
            client.create_table(table)
        self.__client = client
        return client

    def insert(self, item_id: str, item: T):
        for table, values_getter in self._tables.items():
            commit_required = False

            batch = self._batch_factory()
            for value in values_getter(item):
                batch.insert_or_replace_entity({
                    'PartitionKey': value,
                    'RowKey': item_id,
                })
                commit_required = True

            if commit_required:
                self._client.commit_batch(table, batch)
