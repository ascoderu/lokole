from unittest import TestCase
from unittest.mock import PropertyMock
from unittest.mock import patch

from libcloud.common.types import LibcloudError
from libcloud.dns.base import Record
from libcloud.dns.types import RecordType
from libcloud.dns.base import Zone

from opwen_email_server.services.dns import DeleteMxRecords
from opwen_email_server.services.dns import SetupMxRecords
from tests.opwen_email_server.helpers import throw


class DeleteMxRecordsTests(TestCase):
    def test_does_not_make_request_when_key_is_missing(self):
        action = DeleteMxRecords(account='', secret='', provider='CLOUDFLARE')

        with patch.object(action, 'log_warning') as mock_log_warning:
            action(domain='')

        self.assertEqual(mock_log_warning.call_count, 1)

    def test_makes_request_when_key_is_set(self):
        action = DeleteMxRecords('my-user', 'my-key', provider='CLOUDFLARE')

        with patch.object(action, '_driver', new_callable=PropertyMock) as mock_driver:
            zones = [
                Zone(id='1', domain='foo.com', type='master', ttl=1, driver=mock_driver),
                Zone(id='2', domain='my-zone', type='master', ttl=1, driver=mock_driver),
            ]

            records = [
                Record(id='1', name='bar', type=RecordType.A, data='', zone=zones[1], ttl=1, driver=mock_driver),
                Record(id='2', name='my-domain', type=RecordType.MX, data='', zone=zones[1], ttl=1, driver=mock_driver),
            ]

            mock_driver.iterate_zones.return_value = zones
            mock_driver.iterate_records.return_value = records

            action('my-domain.my-zone')

            self.assertEqual(mock_driver.iterate_zones.call_count, 1)
            self.assertEqual(mock_driver.iterate_records.call_count, 1)
            self.assertEqual(mock_driver.delete_record.call_count, 1)

    def test_handles_missing_record(self):
        action = DeleteMxRecords('my-user', 'my-key', provider='CLOUDFLARE')

        with patch.object(action, '_driver', new_callable=PropertyMock) as mock_driver:
            zones = [
                Zone(id='2', domain='my-zone', type='master', ttl=1, driver=mock_driver),
            ]

            records = [
                Record(id='1', name='bar', type=RecordType.A, data='', zone=zones[0], ttl=1, driver=mock_driver),
            ]

            mock_driver.iterate_zones.return_value = zones
            mock_driver.iterate_records.return_value = records

            action('my-domain.my-zone')

            self.assertEqual(mock_driver.iterate_zones.call_count, 1)
            self.assertEqual(mock_driver.iterate_records.call_count, 1)
            self.assertEqual(mock_driver.delete_record.call_count, 0)


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

    def test_returns_when_record_already_exists(self):
        action = SetupMxRecords('my-user', 'my-key', provider='CLOUDFLARE')

        with patch.object(action, '_driver', new_callable=PropertyMock) as mock_driver:
            mock_driver.iterate_zones.return_value = [
                Zone(id='1', domain='foo.com', type='master', ttl=1, driver=mock_driver),
                Zone(id='2', domain='my-zone', type='master', ttl=1, driver=mock_driver),
            ]
            mock_driver.create_record.side_effect = throw(
                LibcloudError('81057: The record already exists.', mock_driver))

            action('my-domain.my-zone')

            self.assertEqual(mock_driver.iterate_zones.call_count, 1)
            self.assertEqual(mock_driver.create_record.call_count, 1)

    def test_throws_when_error_is_unknown(self):
        action = SetupMxRecords('my-user', 'my-key', provider='CLOUDFLARE')

        with patch.object(action, '_driver', new_callable=PropertyMock) as mock_driver:
            mock_driver.iterate_zones.return_value = [
                Zone(id='1', domain='foo.com', type='master', ttl=1, driver=mock_driver),
                Zone(id='2', domain='my-zone', type='master', ttl=1, driver=mock_driver),
            ]
            mock_driver.create_record.side_effect = throw(LibcloudError('Some unknown error', mock_driver))

            with self.assertRaises(LibcloudError):
                action('my-domain.my-zone')
