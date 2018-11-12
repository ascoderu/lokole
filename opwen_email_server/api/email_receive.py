from typing import Tuple
from uuid import uuid4

from opwen_email_server import events
from opwen_email_server.backend.services import AUTH as CLIENTS
from opwen_email_server.backend.services import SENDGRID_STORAGE as STORAGE
from opwen_email_server.services import tasks
from opwen_email_server.utils.log import LogMixin


class _Receiver(LogMixin):
    def __call__(self, client_id: str, email: str) -> Tuple[str, int]:
        domain = CLIENTS.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        email_id = str(uuid4())

        STORAGE.store_text(email_id, email)

        tasks.inbound_store.delay(email_id)

        self.log_event(events.EMAIL_RECEIVED_FOR_CLIENT, {'domain': domain})  # noqa: E501
        return 'received', 200


receive = _Receiver()
