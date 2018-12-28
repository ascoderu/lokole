from functools import lru_cache
from typing import Optional

from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_server.constants.cache import AUTH_DOMAIN_CACHE_SIZE
from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.log import LogMixin


class AzureAuth(LogMixin):
    def __init__(self, storage: AzureTextStorage) -> None:
        self._storage = storage

    def insert(self, client_id: str, domain: str):
        self._storage.store_text(client_id, domain)
        self._storage.store_text(domain, client_id)
        self.log_debug('Registered client %s at domain %s', client_id, domain)

    def client_id_for(self, domain: str) -> Optional[str]:
        try:
            client_id = self._storage.fetch_text(domain)
        except ObjectDoesNotExistError:
            self.log_debug('Unrecognized domain %s', domain)
            return None
        else:
            self.log_debug('Domain %s has client %s', domain, client_id)
            return client_id

    def domain_for(self, client_id: str) -> Optional[str]:
        try:
            domain = self._domain_for_cached(client_id)
        except ObjectDoesNotExistError:
            self.log_debug('Unrecognized client %s', client_id)
            return None
        else:
            self.log_debug('Client %s has domain %s', client_id, domain)
            return domain

    @lru_cache(maxsize=AUTH_DOMAIN_CACHE_SIZE)
    def _domain_for_cached(self, client_id: str) -> str:
        return self._storage.fetch_text(client_id)
