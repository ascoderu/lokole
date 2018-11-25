import requests

from opwen_email_server.config import CLOUDFLARE_KEY
from opwen_email_server.config import CLOUDFLARE_USER
from opwen_email_server.config import CLOUDFLARE_ZONE
from opwen_email_server.config import SENDGRID_KEY
from opwen_email_server.utils.log import LogMixin

SENDGRID_URL = 'https://api.sendgrid.com/v3/user/webhooks/parse/settings'

INBOX_URL = 'http://mailserver.lokole.ca/api/email/sendgrid/{}'

CLOUDFLARE_URL = 'https://api.cloudflare.com/client/v4/zones' \
                 '/{}/dns_records'.format(CLOUDFLARE_ZONE)


class SetupEmailDns(LogMixin):
    def __call__(self, client_id: str, domain: str):
        self._configure_mailbox(client_id, domain)
        self._configure_mx_record(domain)

    def _configure_mailbox(self, client_id: str, domain: str):
        if not SENDGRID_KEY:
            self.log_info('No key set, skipping mailbox setup for %s', domain)
            return

        requests.post(
            url=SENDGRID_URL,
            json={
                'hostname': domain,
                'url': INBOX_URL.format(client_id),
                'spam_check': True,
                'send_raw': True,
            },
            headers={
                'Authorization': 'Bearer {}'.format(SENDGRID_KEY),
            }
        ).raise_for_status()

    def _configure_mx_record(self, domain: str):
        if not CLOUDFLARE_KEY:
            self.log_info('No key set, skipping MX setup for %s', domain)
            return

        client_name = domain.split('.')[0]

        requests.post(
            url=CLOUDFLARE_URL,
            json={
                'type': 'MX',
                'content': 'mx.sendgrid.net',
                'proxied': False,
                'priority': 1,
                'name': client_name,
            },
            headers={
                'X-Auth-Key': CLOUDFLARE_KEY,
                'X-Auth-Email': CLOUDFLARE_USER,
            }
        ).raise_for_status()


setup_email_dns = SetupEmailDns()


def _cli():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--client_id', required=True)
    parser.add_argument('--domain', required=True)
    args = parser.parse_args()

    setup_email_dns(args.client_id, args.domain)


if __name__ == '__main__':
    _cli()
