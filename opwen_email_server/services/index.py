from re import compile as re_compile
from typing import Callable
from typing import Iterable
from typing import Mapping
from typing import TypeVar

from azure.storage.table import TableBatch
from azure.storage.table import TableService

from opwen_email_server.utils.collections import chunks
from opwen_email_server.utils.log import LogMixin

T = TypeVar('T')


class AzureIndex(LogMixin):
    _BATCH_MAX_SIZE = 100
    _PARTITIONKEY_MAX_LENGTH = 1000
    _PARTITIONKEY_INVALID = re_compile('[\\\\/#?\u0000-\u001f\u007f-\u009f]')

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
            for value in values_getter(item):
                value = self._sanitize(value)
                self._client.insert_or_replace_entity(table, {
                    'PartitionKey': value,
                    'RowKey': item_id,
                })
                self.log_debug('inserted %s/%s/%s', table, value, item_id)

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
        num_deleted = 0
        for chunk in chunks(item_ids, self._BATCH_MAX_SIZE):
            batch = self._batch_factory()
            for item_id in chunk:
                batch.delete_entity(partition, item_id)
                num_deleted += 1
                self.log_debug('deleted %s/%s/%s', table, partition, item_id)
            self._client.commit_batch(table, batch)
        self.log_debug('deleted %d from %s/%s', num_deleted, table, partition)

    @classmethod
    def _sanitize(cls, value: str) -> str:
        if not value:
            return value

        value = cls._PARTITIONKEY_INVALID.sub('', value)
        value = value[:cls._PARTITIONKEY_MAX_LENGTH]
        return value
