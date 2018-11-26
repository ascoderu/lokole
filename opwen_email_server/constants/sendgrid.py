from typing_extensions import Final  # noqa: F401

MAILBOX_URL = 'https://api.sendgrid.com/v3/user/webhooks/parse/settings'  # type: Final  # noqa: E501

INBOX_URL = 'http://mailserver.lokole.ca/api/email/sendgrid/{}'  # type: Final

MX_RECORD = 'mx.sendgrid.net'  # type: Final
