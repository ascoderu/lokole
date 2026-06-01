from cached_property import cached_property
from libcloud.common.types import LibcloudError
from libcloud.dns.base import DNSDriver
from libcloud.dns.base import Zone
from libcloud.dns.providers import get_driver
from libcloud.dns.types import Provider
from libcloud.dns.types import RecordAlreadyExistsError
from libcloud.dns.types import RecordType

from opwen_email_server.constants.sendgrid import MX_RECORD
from opwen_email_server.utils.log import LogMixin


class _MxRecords(LogMixin):

    def __init__(self, account: str, secret: str, provider: str) -> None:
        self._account = account
        self._secret = secret
        self._provider = getattr(Provider, provider)

    @cached_property
    def _driver(self) -> DNSDriver:
        driver = get_driver(self._provider)
        return driver(self._account, self._secret)

    def __call__(self, domain: str) -> None:
        if not self._secret:
            self.log_warning('No key, skipping MX setup for %s', domain)
            return

        domain_parts = domain.split('.')
        client_name = domain_parts[0]
        zone_name = '.'.join(domain_parts[1:])

        zone = next(zone for zone in self._driver.iterate_zones() if zone.domain == zone_name)

        self._run(client_name, zone)

    def _run(self, client_name: str, zone: Zone) -> None:
        raise NotImplementedError  # pragma: no cover


class DeleteMxRecords(_MxRecords):

    def _run(self, client_name: str, zone: Zone) -> None:
        try:
            record = next(record for record in self._driver.iterate_records(zone) if record.name == client_name)
        except StopIteration:
            self.log_warning('No MX records for client %s.%s exist', client_name, zone.domain)
        else:
            self._driver.delete_record(record)
            self.log_info('Deleted MX records for client %s.%s', client_name, zone.domain)


class SetupMxRecords(_MxRecords):

    def _run(self, client_name: str, zone: Zone) -> None:
        try:
            self._driver.create_record(
                zone=zone,
                name=client_name,
                type=RecordType.MX,
                data=MX_RECORD,
                extra={'priority': 0},
            )
        except RecordAlreadyExistsError:
            # Record exists - verify it points to the correct mail server
            try:
                existing_record = next(
                    record for record in self._driver.iterate_records(zone)
                    if record.name == client_name and record.type == RecordType.MX
                )
            except StopIteration:
                # Shouldn't happen, but handle gracefully
                self.log_warning('MX record exists but could not be found for %s.%s', client_name, zone.domain)
                return

            if existing_record.data != MX_RECORD:
                # Update to point to correct mail server
                self._driver.update_record(
                    record=existing_record,
                    name=client_name,
                    type=RecordType.MX,
                    data=MX_RECORD,
                    extra={'priority': 0},
                )
                self.log_info('Updated MX records for client %s.%s from %s to %s',
                             client_name, zone.domain, existing_record.data, MX_RECORD)
            else:
                self.log_info('MX records for client %s.%s already exist with correct value', client_name, zone.domain)
        else:
            self.log_info('Set up MX records for client %s.%s', client_name, zone.domain)
