from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from connexion.decorators.security import validate_scope
from responses import mock as mock_responses

from opwen_email_server.constants import github
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.auth import BasicAuth
from opwen_email_server.services.auth import GithubAuth
from opwen_email_server.services.auth import NoAuth
from opwen_email_server.services.storage import AzureObjectStorage
from tests.opwen_email_server.helpers import MockResponses


class BasicAuthTests(TestCase):
    def setUp(self):
        self._auth = BasicAuth({
            'user1': {'password': 'pass', 'scopes': {'scope1', 'scopeA'}},
            'user2': {'password': 'pass2'},
        })

    def test_with_bad_user(self):
        self.assertIsNone(self._auth(username='', password='pass'))

    def test_with_missing_user(self):
        self.assertIsNone(self._auth(username='does-not-exist', password='pass'))

    def test_with_bad_password(self):
        self.assertIsNone(self._auth(username='user1', password='incorrect'))

    def test_with_correct_password(self):
        self.assertIsNotNone(self._auth(username='user2', password='pass2'))

        self.assertIsNotNone(self._auth(username='user1', password='pass'))

        self.assertIsNotNone(self._auth(username='user1', password='pass', required_scopes=['scope1']))

        self.assertIsNotNone(self._auth(username='user1', password='pass', required_scopes=['scope1', 'scopeA']))


class GithubAuthTests(TestCase):
    def setUp(self):
        self._auth = GithubAuth(organization='organization', page_size=2)

    def test_with_bad_arguments(self):
        self.assertIsNone(self._auth(access_token=''))

    @mock_responses.activate
    def test_with_missing_team(self):
        mock_responses.add(
            mock_responses.POST,
            github.GRAPHQL_URL,
            body='''{
                "data": {
                    "viewer": {
                        "login": "user",
                        "organization": {
                            "teams": {
                                "edges": [
                                    {"cursor": "cursor1"}
                                ],
                                "nodes": [
                                    {"slug": "team1"}
                                ]
                            }
                        }
                    }
                }
            }''',
            status=200,
        )

        user = self._auth(access_token='token')

        self.assertIsNotNone(user)
        self.assertEqual(user['sub']['name'], 'user')
        self.assertFalse(validate_scope(['team2'], user['scope']))

    @mock_responses.activate
    def test_with_bad_password(self):
        mock_responses.add(
            mock_responses.POST,
            github.GRAPHQL_URL,
            json={'message': 'Bad credentials'},
            status=401,
        )

        user = self._auth(access_token='incorrect')

        self.assertIsNone(user)

    @mock_responses.activate
    def test_with_correct_password(self):
        mock_responses.add_callback(
            mock_responses.POST,
            github.GRAPHQL_URL,
            callback=MockResponses([
                '''{
                       "data": {
                           "viewer": {
                               "login": "user",
                               "organization": {
                                   "teams": {
                                       "edges": [
                                           {"cursor": "cursor1"},
                                           {"cursor": "cursor2"}
                                       ],
                                       "nodes": [
                                           {"slug": "team1"},
                                           {"slug": "team2"}
                                       ]
                                   }
                               }
                           }
                       }
                }''',
                '''{
                       "data": {
                           "viewer": {
                               "login": "user",
                               "organization": {
                                   "teams": {
                                       "edges": [
                                           {"cursor": "cursor3"}
                                       ],
                                       "nodes": [
                                           {"slug": "team3"}
                                       ]
                                   }
                               }
                           }
                       }
                }''',
            ]),
        )

        user = self._auth(access_token='access_token')

        self.assertIsNotNone(user)
        self.assertEqual(user['sub']['name'], 'user')
        self.assertTrue(validate_scope(['team3'], user['scope']))


class AzureAuthTests(TestCase):
    def setUp(self):
        self._folder = mkdtemp()
        self._storage = AzureObjectStorage(
            account=self._folder,
            key='key',
            container='auth',
            provider='LOCAL',
        )
        self._auth = AzureAuth(storage=self._storage, sudo_scope='sudo')

    def tearDown(self):
        rmtree(self._folder)

    def test_inserts_and_retrieves_client(self):
        self._auth.insert('client', 'domain', {'name': 'owner'})
        self.assertEqual(self._auth.domain_for('client'), 'domain')
        self.assertEqual(self._auth.client_id_for('domain'), 'client')
        self.assertIsNone(self._auth.domain_for('unknown-client'))
        self.assertIsNone(self._auth.client_id_for('unknown-client'))
        self.assertTrue(self._auth.is_owner('domain', {'name': 'owner'}))
        self.assertFalse(self._auth.is_owner('domain', {'name': 'unknown-user'}))
        self.assertFalse(self._auth.is_owner('unknown-domain', {'name': 'owner'}))

    def test_lists_domains(self):
        self._auth.insert('client1', 'domain1', {'name': 'owner1'})
        self._auth.insert('client2', 'domain2', {'name': 'owner2'})
        self.assertEqual(sorted(self._auth.domains()), sorted(['domain1', 'domain2']))

    def test_deletes_client(self):
        self._auth.insert('client', 'domain', {'name': 'owner'})
        self.assertIsNotNone(self._auth.domain_for('client'))
        self._auth.delete('client', 'domain')
        self.assertIsNone(self._auth.domain_for('client'))

    def test_is_owner_with_sudo(self):
        self._auth.insert('client', 'domain', {'name': 'owner'})
        self.assertFalse(self._auth.is_owner('domain', {'name': 'user'}))
        self.assertTrue(self._auth.is_owner('domain', {'name': 'owner'}))
        self.assertTrue(self._auth.is_owner('domain', {'name': 'sudo', 'scopes': ['sudo']}))


class NoAuthTests(TestCase):
    def setUp(self):
        self._auth = NoAuth()

    def test_does_not_validate_owner(self):
        self._auth.insert('client', 'domain', {'name': 'owner'})
        self.assertTrue(self._auth.is_owner('domain', {'name': 'owner'}))
        self.assertTrue(self._auth.is_owner('domain', {'name': 'unknown-user'}))
        self.assertTrue(self._auth.is_owner('unknown-domain', {'name': 'owner'}))

    def test_delete_has_no_effect(self):
        self._auth.insert('client', 'domain', {'name': 'owner'})
        self.assertIsNotNone(self._auth.domain_for('client'))
        self._auth.delete('client', 'domain')
        self.assertIsNotNone(self._auth.domain_for('client'))

    def test_lists_no_domains(self):
        self._auth.insert('client1', 'domain1', {'name': 'owner1'})
        self._auth.insert('client2', 'domain2', {'name': 'owner2'})
        self.assertEqual(self._auth.domains(), [])
