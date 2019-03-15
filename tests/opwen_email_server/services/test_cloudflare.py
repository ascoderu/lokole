from unittest import TestCase
from unittest.mock import patch

from responses import mock as mock_responses

from opwen_email_server.services.cloudflare import SetupCloudflareMxRecords


class SetupCloudflareMxRecordsTests(TestCase):
    def test_does_not_make_request_when_key_is_missing(self):
        action = SetupCloudflareMxRecords(user='', key='', zone='')

        with patch.object(action, 'log_warning') as mock_log_warning:
            action(domain='')

        self.assertEqual(mock_log_warning.call_count, 1)

    @mock_responses.activate
    def test_makes_request_when_key_is_set(self):
        mock_responses.add(
            mock_responses.POST,
            'https://api.cloudflare.com/client/v4/zones/my-zone/dns_records')

        action = SetupCloudflareMxRecords('my-user', 'my-key', 'my-zone')

        action('my-domain')

        self.assertEqual(len(mock_responses.calls), 1)
        self.assertIn(b'"name": "my-domain"',
                      mock_responses.calls[0].request.body)
