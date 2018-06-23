from opwen_email_server import events
from opwen_email_server.backend import email_sender
from opwen_email_server.backend import server_datastore
from opwen_email_server.utils.email_parser import get_domain
from opwen_email_server.utils.log import LogMixin


class _Sender(LogMixin):
    def __call__(self, resource_id: str):
        email = server_datastore.fetch_email(resource_id)

        email_sender.send(email)

        self.log_event(events.EMAIL_DELIVERED_FROM_CLIENT, {'domain': get_domain(email.get('from', ''))})  # noqa: E501
        return 'OK', 200


send = _Sender()
