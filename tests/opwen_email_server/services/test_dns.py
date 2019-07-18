from unittest import TestCase
from unittest.mock import PropertyMock
from unittest.mock import patch

from libcloud.dns.base import Zone

from opwen_email_server.services.dns import SetupMxRecords


class SetupMxRecordsTests(TestCase):
    def test_does_not_make_request_when_key_is_missing(self):
        action = SetupMxRecords(account='', secret='', provider='CLOUDFLARE')

        with patch.object(action, 'log_warning') as mock_log_warning:
            action(domain='')

        self.assertEqual(mock_log_warning.call_count, 1)

    def test_makes_request_when_key_is_set(self):
        action = SetupMxRecords('my-user', 'my-key', provider='CLOUDFLARE')

        with patch.object(action, '_driver', new_callable=PropertyMock) as mock_driver:
            mock_driver.iterate_zones.return_value = [
                Zone(id='1', domain='foo.com', type='master', ttl=1, driver=mock_driver),
                Zone(id='2', domain='my-zone', type='master', ttl=1, driver=mock_driver),
            ]

            action('my-domain.my-zone')

            self.assertEqual(mock_driver.iterate_zones.call_count, 1)
            self.assertEqual(mock_driver.create_record.call_count, 1)
