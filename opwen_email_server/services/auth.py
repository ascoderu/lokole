from ast import literal_eval

from os import environ
from typing import Callable
from typing import Mapping

from opwen_email_server.utils.log import LogMixin


class EnvironmentAuth(LogMixin):
    def __init__(self, client_to_domain: Mapping[str, str]=None,
                 envgetter: Callable[[str, str], str]=environ.get,
                 envkey: str='LOKOLE_CLIENTS') -> None:

        self.__client_to_domain = dict(client_to_domain or {})
        self._envgetter = envgetter
        self._envkey = envkey

    @property
    def _client_to_domain(self):
        if not self.__client_to_domain:
            self.__client_to_domain = self._create_client_to_domain()
            self.log_debug('initialized auth to %r', self.__client_to_domain)
        return self.__client_to_domain

    def _create_client_to_domain(self) -> Mapping[str, str]:
        client_to_domain = literal_eval(self._envgetter(self._envkey, '{}'))
        if not client_to_domain:
            raise ValueError('environment key {} not set'.format(self._envkey))
        return client_to_domain

    def __contains__(self, client: str) -> bool:
        return client in self._client_to_domain

    def domain_for(self, client: str) -> str:
        return self._client_to_domain[client]
