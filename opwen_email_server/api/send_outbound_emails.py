from typing import Tuple

from opwen_email_server import config
from opwen_email_server import events
from opwen_email_server.backend import server_datastore
from opwen_email_server.services.sendgrid import SendgridEmailSender
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.log import LogMixin

EMAIL = SendgridEmailSender(key=config.EMAIL_SENDER_KEY)


class _Sender(LogMixin):
    def __call__(self, resource_id: str) -> Tuple[str, int]:
        email = server_datastore.fetch_email(resource_id)

        success = EMAIL.send_email(email)
        if not success:
            return 'error', 500

        self.log_event(events.EMAIL_DELIVERED_FROM_CLIENT, {'domain': get_domain(email.get('from', ''))})  # noqa: E501
        return 'OK', 200


send = _Sender()
