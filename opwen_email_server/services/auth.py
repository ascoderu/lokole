from abc import ABCMeta
from abc import abstractmethod
from typing import Callable
from typing import Optional

from azure.storage.table import TableService


class Auth(metaclass=ABCMeta):
    @abstractmethod
    def domain_for(self, client_id: str) -> Optional[str]:
        raise NotImplementedError  # pramga: no cover


class AzureAuth(Auth):
    def __init__(self, account: str, key: str, table: str,
                 client: TableService=None,
                 client_factory: Callable[..., TableService]=TableService
                 ) -> None:

        self._account = account
        self._key = key
        self._table = table
        self.__client = client
        self._client_factory = client_factory

    @property
    def _client(self) -> TableService:
        if self.__client is not None:
            return self.__client
        client = self._client_factory(self._account, self._key)
        client.create_table(self._table)
        self.__client = client
        return client

    def insert(self, client_id: str, domain: str):
        self._client.insert_entity(self._table, {
            'RowKey': client_id,
            'PartitionKey': client_id,
            'domain': domain,
        })

    def domain_for(self, client_id):
        query = "PartitionKey eq '{0}' and RowKey eq '{0}'".format(client_id)
        entities = self._client.query_entities(self._table, query)
        for entity in entities:
            domain = entity.get('domain')
            if domain:
                return domain
        return None
