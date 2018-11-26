import requests

from opwen_email_server.constants.cloudflare import DNS_URL
from opwen_email_server.constants.sendgrid import MX_RECORD
from opwen_email_server.utils.log import LogMixin


class SetupCloudflareMxRecords(LogMixin):
    def __init__(self, user: str, key: str, zone: str) -> None:
        self._user = user
        self._key = key
        self._zone = zone

    def __call__(self, domain: str) -> None:
        if not self._key:
            self.log_warning('No key, skipping MX setup for %s', domain)
            return

        client_name = domain.split('.')[0]

        requests.post(
            url=DNS_URL.format(self._zone),
            json={
                'type': 'MX',
                'content': MX_RECORD,
                'proxied': False,
                'priority': 1,
                'name': client_name,
            },
            headers={
                'X-Auth-Key': self._key,
                'X-Auth-Email': self._user,
            }
        ).raise_for_status()

        self.log_debug('Set up mx records for %s', domain)
