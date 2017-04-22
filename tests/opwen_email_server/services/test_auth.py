from unittest import TestCase
from unittest.mock import Mock

from opwen_email_server.services.auth import AzureAuth


class AzureAuthTests(TestCase):
    # noinspection PyTypeChecker
    def setUp(self):
        self.mock_client = Mock()
        self.auth = AzureAuth(account='account', key='key', table='table',
                              client=self.mock_client)

    def test_retrieves_inserted(self):
        self.given_clients(('client', 'domain'))

        actual_domain = self.auth.domain_for('client')

        self.assertEqual(actual_domain, 'domain')

    def test_retrieves_none_for_missing(self):
        self.given_clients()

        actual_domain = self.auth.domain_for('client')

        self.assertIsNone(actual_domain)

    def given_clients(self, *clients_and_domains):
        self.mock_client.query_entities.return_value = ({
            'RowKey': client_id,
            'PartitionKey': client_id,
            'domain': domain
        } for (client_id, domain) in clients_and_domains)
