from contextlib import contextmanager

from opwen_email_server.services.auth import EnvironmentAuth


class AuthTestMixin(object):
    @contextmanager
    def given_clients(self, package, clients):
        original_clients = getattr(package, 'CLIENTS')
        setattr(package, 'CLIENTS', EnvironmentAuth(clients))
        yield
        setattr(package, 'CLIENTS', original_clients)
