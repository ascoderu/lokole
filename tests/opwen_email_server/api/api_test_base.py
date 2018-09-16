from contextlib import contextmanager
from typing import Mapping
from typing import Optional


class FakeAuth(object):
    def __init__(self, clients: Mapping[str, str]):
        self._clients = dict(clients.items())

    def domain_for(self, client_id: str) -> Optional[str]:
        return self._clients.get(client_id)


class AuthTestMixin(object):
    @contextmanager
    def given_clients(self, package, clients: Mapping[str, str]):
        original_clients = getattr(package, 'CLIENTS')
        setattr(package, 'CLIENTS', FakeAuth(clients))
        yield
        setattr(package, 'CLIENTS', original_clients)
