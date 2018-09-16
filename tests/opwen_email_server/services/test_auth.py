from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from opwen_email_server.services.auth import AzureAuth


class AzureAuthTests(TestCase):
    def setUp(self):
        self._folder = mkdtemp()
        self._auth = AzureAuth(account=self._folder, key='key',
                               table='auth', provider='LOCAL')

    def tearDown(self):
        rmtree(self._folder)

    def test_inserts_and_retrieves_client(self):
        self._auth.insert('client', 'domain')
        self.assertEqual(self._auth.domain_for('client'), 'domain')
        self.assertIsNone(self._auth.domain_for('unknown-client'))
