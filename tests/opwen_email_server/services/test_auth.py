from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.storage import AzureTextStorage


class AzureAuthTests(TestCase):
    def setUp(self):
        self._folder = mkdtemp()
        self._auth = AzureAuth(
            storage=AzureTextStorage(
                account=self._folder,
                key='key',
                container='auth',
                provider='LOCAL'))

    def tearDown(self):
        rmtree(self._folder)

    def test_inserts_and_retrieves_client(self):
        self._auth.insert('client', 'domain')
        self.assertEqual(self._auth.domain_for('client'), 'domain')
        self.assertEqual(self._auth.client_id_for('domain'), 'client')
        self.assertIsNone(self._auth.domain_for('unknown-client'))
        self.assertIsNone(self._auth.client_id_for('unknown-client'))
