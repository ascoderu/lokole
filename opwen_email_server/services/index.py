from typing import Callable
from typing import Generic
from typing import Iterable
from typing import Mapping
from typing import TypeVar

from azure.storage.table import TableBatch
from azure.storage.table import TableService

from opwen_email_server.utils.log import LogMixin

T = TypeVar('T')


class AzureIndex(LogMixin, Generic[T]):
    def __init__(self, account: str, key: str,
                 tables: Mapping[str, Callable[[T], Iterable[str]]],
                 client: TableService=None,
                 client_factory: Callable[..., TableService]=TableService,
                 batch_factory: Callable[..., TableBatch]=TableBatch) -> None:

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
                self.log_debug('inserted %s into %s/%s', item_id, table, value)

            if commit_required:
                self._client.commit_batch(table, batch)

    def query(self, table: str, partition: str) -> Iterable[str]:
        search_query = "PartitionKey eq '{}'".format(partition)
        entities = self._client.query_entities(table, search_query)
        num_fetched = 0
        for entity in entities:
            item_id = entity['RowKey']
            num_fetched += 1
            yield item_id
        self.log_debug('fetched %d from %s/%s', num_fetched, table, partition)

    def delete(self, table: str, partition: str, item_ids: Iterable[str]):
        batch = self._batch_factory()
        num_deleted = 0
        for item_id in item_ids:
            batch.delete_entity(partition, item_id)
            num_deleted += 1
        self._client.commit_batch(table, batch)
        self.log_debug('deleted %d from %s/%s', num_deleted, table, partition)
