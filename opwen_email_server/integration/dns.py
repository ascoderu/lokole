from opwen_email_server.config import CLOUDFLARE_KEY
from opwen_email_server.config import CLOUDFLARE_USER
from opwen_email_server.config import CLOUDFLARE_ZONE
from opwen_email_server.config import SENDGRID_KEY
from opwen_email_server.services.cloudflare import SetupCloudflareMxRecords
from opwen_email_server.services.sendgrid import SetupSendgridMailbox
from opwen_email_server.utils.log import LogMixin


class SetupEmailDns(LogMixin):
    def __call__(self, client_id: str, domain: str):
        SetupSendgridMailbox(SENDGRID_KEY)(client_id, domain)
        SetupCloudflareMxRecords(CLOUDFLARE_USER, CLOUDFLARE_KEY, CLOUDFLARE_ZONE)(domain)


def _cli():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('--client_id', required=True)
    parser.add_argument('--domain', required=True)
    args = parser.parse_args()

    setup_email_dns = SetupEmailDns()
    setup_email_dns(args.client_id, args.domain)


if __name__ == '__main__':
    _cli()
