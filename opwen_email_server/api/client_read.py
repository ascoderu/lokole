from typing import Tuple
from typing import Union

from opwen_email_server import events
from opwen_email_server.backend import server_datastore
from opwen_email_server.backend.services import AUTH as CLIENTS
from opwen_email_server.backend.services import CLIENT_STORAGE as STORAGE
from opwen_email_server.utils.log import LogMixin


class _Downloader(LogMixin):
    def __call__(self, client_id) -> Union[dict, Tuple[str, int]]:
        domain = CLIENTS.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        delivered = set()

        def mark_delivered(email: dict) -> dict:
            delivered.add(email['_uid'])
            return email

        pending = server_datastore.fetch_pending_emails(domain)
        pending = [mark_delivered(email) for email in pending]

        resource_id = STORAGE.store_objects(pending)

        server_datastore.mark_emails_as_delivered(domain, delivered)

        self.log_event(events.EMAILS_DELIVERED_TO_CLIENT, {'domain': domain, 'num_emails': len(delivered)})  # noqa: E501
        return {
            'resource_id': resource_id,
            'resource_container': STORAGE.container,
            'resource_type': 'azure-blob',
        }


download = _Downloader()
