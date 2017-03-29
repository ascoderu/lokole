from ast import literal_eval
from os import environ
from typing import Callable
from typing import Mapping


class EnvironmentAuth(object):
    def __init__(self, client_to_domain: Mapping[str, str]=None,
                 envgetter: Callable[[str, str], str]=environ.get,
                 envkey: str='LOKOLE_CLIENTS') -> None:

        if client_to_domain is None:
            client_to_domain = dict(literal_eval(envgetter(envkey, '{}')))

        self._client_to_domain = dict(client_to_domain.items())

        if not self._client_to_domain:
            raise ValueError('environment key {} not set'.format(envkey))

    def __contains__(self, client: str) -> bool:
        return client in self._client_to_domain
