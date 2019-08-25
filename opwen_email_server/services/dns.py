from cached_property import cached_property
from libcloud.dns.base import DNSDriver
from libcloud.dns.providers import get_driver
from libcloud.dns.types import Provider
from libcloud.dns.types import RecordType

from opwen_email_server.constants.sendgrid import MX_RECORD
from opwen_email_server.utils.log import LogMixin


class SetupMxRecords(LogMixin):
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

        self._driver.create_record(
            zone=zone,
            name=client_name,
            type=RecordType.MX,
            data=MX_RECORD,
        )

        self.log_debug('Set up MX records for %s', domain)
