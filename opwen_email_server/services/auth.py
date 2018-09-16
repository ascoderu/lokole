from functools import lru_cache
from json import loads
from os import getenv
from typing import Optional

from libcloud.storage.types import ObjectDoesNotExistError

from opwen_email_server.services.storage import AzureTextStorage
from opwen_email_server.utils.log import LogMixin


class AzureAuth(LogMixin):
    def __init__(self, account: str, key: str, table: str,
                 provider: str) -> None:
        self._storage = AzureTextStorage(account, key, table, provider)

        for client in loads(getenv('LOKOLE_DEFAULT_CLIENTS', '[]')):
            self.insert(client['id'], client['domain'])

    def insert(self, client_id: str, domain: str):
        self._storage.store_text(client_id, domain)
        self.log_debug('Registered client %s at domain %s', client_id, domain)

    def domain_for(self, client_id: str) -> Optional[str]:
        try:
            domain = self._domain_for_cached(client_id)
        except ObjectDoesNotExistError:
            self.log_debug('Unrecognized client %s', client_id)
            return None
        else:
            self.log_debug('Client %s has domain %s', client_id, domain)
            return domain

    @lru_cache(maxsize=128)
    def _domain_for_cached(self, client_id: str) -> str:
        return self._storage.fetch_text(client_id)
