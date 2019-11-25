from typing_extensions import Final  # noqa: F401

MAILBOX_CREATE_URL = 'https://api.sendgrid.com/v3/user/webhooks/parse/settings'  # type: Final  # noqa: E501  # yapf: disable
MAILBOX_DETAIL_URL = 'https://api.sendgrid.com/v3/user/webhooks/parse/settings/{}'  # type: Final  # noqa: E501  # yapf: disable

INBOX_URL = 'https://mailserver.lokole.ca/api/email/sendgrid/{}'  # type: Final

MX_RECORD = 'mx.sendgrid.net'  # type: Final
