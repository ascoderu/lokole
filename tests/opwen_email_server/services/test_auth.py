from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase
from unittest.mock import Mock

from responses import mock as mock_responses

from opwen_email_server.constants import github
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.auth import AnyOfBasicAuth
from opwen_email_server.services.auth import BasicAuth
from opwen_email_server.services.auth import GithubBasicAuth
from opwen_email_server.services.storage import AzureObjectStorage
from tests.opwen_email_server.helpers import MockResponses


class AnyOfBasicAuthTests(TestCase):
    def setUp(self):
        self._auth1 = Mock()
        self._auth2 = Mock()
        self._auth3 = Mock()
        self._auth = AnyOfBasicAuth(auths=[self._auth1, self._auth2, self._auth3])

    def test_with_failing_sub_auth(self):
        self._auth1.return_value = None
        self._auth2.return_value = None
        self._auth3.return_value = None

        user = self._auth('username', 'password')

        self.assertIsNone(user)
        self.assertEqual(self._auth1.call_count, 1)
        self.assertEqual(self._auth2.call_count, 1)
        self.assertEqual(self._auth3.call_count, 1)

    def test_with_passing_sub_auth(self):
        self._auth1.return_value = None
        self._auth2.return_value = {'sub': 'username'}
        self._auth3.return_value = None

        user = self._auth('username', 'password')

        self.assertIsNotNone(user)
        self.assertEqual(self._auth1.call_count, 1)
        self.assertEqual(self._auth2.call_count, 1)
        self.assertEqual(self._auth3.call_count, 0)


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

    def test_with_missing_scope(self):
        self.assertIsNone(self._auth(username='user1', password='pass', required_scopes=['scope2']))

        self.assertIsNone(self._auth(username='user1', password='pass', required_scopes=['scope1', 'scope2']))

    def test_with_correct_password(self):
        self.assertIsNotNone(self._auth(username='user2', password='pass2'))

        self.assertIsNotNone(self._auth(username='user1', password='pass'))

        self.assertIsNotNone(self._auth(username='user1', password='pass', required_scopes=['scope1']))

        self.assertIsNotNone(self._auth(username='user1', password='pass', required_scopes=['scope1', 'scopeA']))


class GithubBasicAuthTests(TestCase):
    def setUp(self):
        self._auth = GithubBasicAuth(organization='organization', team='team', page_size=2)

    def test_with_bad_user(self):
        self.assertIsNone(self._auth(username='', password='pass'))

    @mock_responses.activate
    def test_with_missing_user(self):
        mock_responses.add(
            mock_responses.POST,
            github.GRAPHQL_URL,
            body='''{
                "data": {
                    "organization": {
                        "team": {
                            "members": {
                                "edges": [
                                    {"cursor": "cursor1"}
                                ],
                                "nodes": [
                                    {"login": "user1"}
                                ]
                            }
                        }
                    }
                }
            }''',
            status=200,
        )

        self.assertIsNone(self._auth(username='does-not-exist', password='pass'))

    @mock_responses.activate
    def test_with_bad_password(self):
        mock_responses.add(
            mock_responses.POST,
            github.GRAPHQL_URL,
            json={'message': 'Bad credentials'},
            status=401,
        )

        self.assertIsNone(self._auth(username='user1', password='incorrect'))

    @mock_responses.activate
    def test_with_correct_password(self):
        mock_responses.add_callback(
            mock_responses.POST,
            github.GRAPHQL_URL,
            callback=MockResponses([
                '''{
                       "data": {
                           "organization": {
                               "team": {
                                   "members": {
                                       "edges": [
                                           {"cursor": "cursor1"},
                                           {"cursor": "cursor2"}
                                       ],
                                   "nodes": [
                                       {"login": "user1"},
                                       {"login": "user2"}
                                   ]
                               }
                           }
                       }
                   }
                }''',
                '''{
                       "data": {
                           "organization": {
                               "team": {
                                   "members": {
                                       "edges": [
                                           {"cursor": "cursor3"}
                                       ],
                                   "nodes": [
                                       {"login": "user3"}
                                   ]
                               }
                           }
                       }
                   }
                }''',
            ]),
        )

        self.assertIsNotNone(self._auth(username='user3', password='pass'))


class AzureAuthTests(TestCase):
    def setUp(self):
        self._folder = mkdtemp()
        self._storage = AzureObjectStorage(
            account=self._folder,
            key='key',
            container='auth',
            provider='LOCAL',
        )
        self._auth = AzureAuth(storage=self._storage)

    def tearDown(self):
        rmtree(self._folder)

    def test_inserts_and_retrieves_client(self):
        self._auth.insert('client', 'domain', 'owner')
        self.assertEqual(self._auth.domain_for('client'), 'domain')
        self.assertEqual(self._auth.client_id_for('domain'), 'client')
        self.assertIsNone(self._auth.domain_for('unknown-client'))
        self.assertIsNone(self._auth.client_id_for('unknown-client'))
        self.assertTrue(self._auth.is_owner('domain', 'owner'))
        self.assertFalse(self._auth.is_owner('domain', 'unknown-user'))
        self.assertFalse(self._auth.is_owner('unknown-domain', 'owner'))

    def test_lists_domains(self):
        self._auth.insert('client1', 'domain1', 'owner1')
        self._auth.insert('client2', 'domain2', 'owner2')
        self.assertEqual(sorted(self._auth.domains()), sorted(['domain1', 'domain2']))

    def test_deletes_client(self):
        self._auth.insert('client', 'domain', 'owner')
        self.assertIsNotNone(self._auth.domain_for('client'))
        self._auth.delete('client', 'domain')
        self.assertIsNone(self._auth.domain_for('client'))
