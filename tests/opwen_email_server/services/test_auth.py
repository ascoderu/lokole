from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.auth import BasicAuth
from opwen_email_server.services.storage import AzureTextStorage


class BasicAuthTests(TestCase):
    def setUp(self):
        self._auth = BasicAuth({
            'user1': {'password': 'pass', 'scopes': {'scope1', 'scopeA'}},
            'user2': {'password': 'pass2'},
        })

    def test_with_bad_user(self):
        self.assertIsNone(
            self._auth(username='', password='pass'))

    def test_with_missing_user(self):
        self.assertIsNone(
            self._auth(username='does-not-exist', password='pass'))

    def test_with_bad_password(self):
        self.assertIsNone(
            self._auth(username='user1', password='incorrect'))

    def test_with_missing_scope(self):
        self.assertIsNone(
            self._auth(username='user1', password='pass',
                       required_scopes=['scope2']))

        self.assertIsNone(
            self._auth(username='user1', password='pass',
                       required_scopes=['scope1', 'scope2']))

    def test_with_correct_password(self):
        self.assertIsNotNone(
            self._auth(username='user2', password='pass2'))

        self.assertIsNotNone(
            self._auth(username='user1', password='pass'))

        self.assertIsNotNone(
            self._auth(username='user1', password='pass',
                       required_scopes=['scope1']))

        self.assertIsNotNone(
            self._auth(username='user1', password='pass',
                       required_scopes=['scope1', 'scopeA']))


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
