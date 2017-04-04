from contextlib import contextmanager
from unittest import TestCase

from opwen_email_server.api import client_read
from opwen_email_server.services.auth import EnvironmentAuth


class DownloadTests(TestCase):
    def test_denies_unknown_client(self):
        with self.given_clients({'client1': 'id1'}):
            message, status = client_read.download('unknown_client')
            self.assertEqual(status, 403)

    @contextmanager
    def given_clients(self, clients):
        original_clients = client_read.CLIENTS
        client_read.CLIENTS = EnvironmentAuth(clients)
        yield
        client_read.CLIENTS = original_clients
