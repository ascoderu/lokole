from abc import ABCMeta
from abc import abstractmethod
from functools import lru_cache
from typing import Callable
from typing import Optional

from azure.storage.table import TableService

from opwen_email_server.utils.log import LogMixin


class Auth(metaclass=ABCMeta):
    @abstractmethod
    def domain_for(self, client_id: str) -> Optional[str]:
        raise NotImplementedError  # pramga: no cover


class AzureAuth(Auth, LogMixin):
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
        self.log_debug('Registered client %s at domain %s', client_id, domain)

    def domain_for(self, client_id):
        try:
            return self._domain_for_cached(client_id)
        except KeyError:
            return None

    @lru_cache(maxsize=128)
    def _domain_for_cached(self, client_id: str) -> str:
        query = "PartitionKey eq '{0}' and RowKey eq '{0}'".format(client_id)
        entities = self._client.query_entities(self._table, query)
        for entity in entities:
            domain = entity.get('domain')
            if domain:
                self.log_debug('Client %s has domain %s', client_id, domain)
                return domain
        self.log_debug('Unrecognized client %s', client_id)
        raise KeyError
