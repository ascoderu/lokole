from typing import Tuple

from opwen_email_server import events
from opwen_email_server.backend.services import AUTH as CLIENTS
from opwen_email_server.services import tasks
from opwen_email_server.utils.log import LogMixin


class _Uploader(LogMixin):
    def __call__(self, client_id: str, upload_info: dict) -> Tuple[str, int]:
        domain = CLIENTS.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        resource_id = upload_info.get('resource_id')

        tasks.written_store.delay(resource_id)

        self.log_event(events.EMAILS_RECEIVED_FROM_CLIENT, {'domain': domain})  # noqa: E501
        return 'uploaded', 200


upload = _Uploader()
