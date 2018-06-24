from typing import Tuple

from opwen_email_server import azure_constants as constants
from opwen_email_server import config
from opwen_email_server import events
from opwen_email_server.services.auth import AzureAuth
from opwen_email_server.services.queue import AzureQueue
from opwen_email_server.utils.log import LogMixin

QUEUE = AzureQueue(namespace=config.QUEUES_NAMESPACE,
                   sas_key=config.QUEUES_SAS_KEY,
                   sas_name=config.QUEUES_SAS_NAME,
                   name=constants.QUEUE_CLIENT_PACKAGE)

CLIENTS = AzureAuth(account=config.TABLES_ACCOUNT, key=config.TABLES_KEY,
                    table=constants.TABLE_AUTH)


class _Uploader(LogMixin):
    def __call__(self, client_id: str, upload_info: dict) -> Tuple[str, int]:
        domain = CLIENTS.domain_for(client_id)
        if not domain:
            self.log_event(events.UNREGISTERED_CLIENT, {'client_id': client_id})  # noqa: E501
            return 'client is not registered', 403

        resource_type = upload_info.get('resource_type')
        resource_id = upload_info.get('resource_id')
        resource_container = upload_info.get('resource_container')

        QUEUE.enqueue({
            '_version': '0.1',
            '_type': 'lokole_emails_received',
            '_resource_type': resource_type,
            'resource_id': resource_id,
            'container_name': resource_container,
        })

        self.log_event(events.EMAILS_RECEIVED_FROM_CLIENT, {'domain': domain})  # noqa: E501
        return 'uploaded', 200


upload = _Uploader()
